import pandas as pd
import numpy as np


def check_for_duplicates(d_corr, ds_corr, tu_corr):
    if (
        d_corr["Donor_ID"].duplicated().any()
        or ds_corr["ID"].duplicated().any()
        or tu_corr["ID"].duplicated().any()
    ):
        raise ValueError(
            f"Duplicate values found in the ID column of at least one of d_corr, ds_corr or tu_corr."
        )

    if (
        d_corr.columns.duplicated().any()
        or ds_corr.columns.duplicated().any()
        or tu_corr.columns.duplicated().any()
    ):
        raise ValueError(
            f"Duplicate column names for at least one of d_corr, ds_corr or tu_corr."
        )


def get_preprocessed_data_anon(db_conn):
    """
    See more documentation in Data analysis documentation Google doc  https://docs.google.com/document/d/12GaFIQO7vWYqfqWGpAt7MmugmfwhMc5-nx_11wYU3g4/edit#


    # Description
    This function is meant to be run before any data analysis.
    This function will read and clean the data from the v_Donors_anon, v_Tax_unit_anon views and the Donations table.

    ## NB
    * These changes are not done in the data base, and only affect the data analysis in python
    * Important to note that all donors without registered donations in the database are filtered out
    * Any test donors are filtered out in the v_Donors_anon view itself
    * Weakness: In this preprocessing of donors, donations and tax_units, we make the assumption that any donor account with the same first and last name belong to the same person. This is a weakness in the processing, since there could be different persons with the same first and last name.
    However, with our current number of donors, we view the benefit of merging greater than the possible disadvantages

    ## Background
    Some donors will create several different donor accounts over the years. Ie. They may use different emails, but still register with the same first and last name or ssn. To make the data analysis more representative of reality, we want to merge the donors accounts we believe belong to the same person.

    ### Merging duplicates on first and last name
    * Donor accounts without names, only whitespaces as names or only a single word as a name will not be matched
    * We choose to keep only the donor with the most recent donation (aka most_recent_donor) for each group of donors with same first and last name. This means that we transfer all donations to this donor, and filter out the other duplicates from the donor dataframe.
    * We only keep the tax_unit-rows from most_recent_donor

    ### Merging duplicates on ssn
    * If one donor has several tax_units with identical ssn's we choose the most recent tax_unit, and remove the duplicate
    * We choose to keep only the donor with the most recent donation (aka most_recent_donor) for each group of donors with same ssn. This means that we transfer all donations to this donor, and filter out the other duplicates from the donor dataframe.
    * We only keep the tax_unit-rows from most_recent_donor

    ### Setting date_registered as the timestamp of the first donation
    * The date_registered column does not always match the timestamp of the first donation. For data analysis purposes, the date_registered column is changed such that it always matches the first registered donation for this donor.


    ### Adding columns with metadata to d_corr
    We add the columns
    * has_business_tu: which is true if the donor has at least one tax_unit with is_business = True, and false otherwise
    * mult_ssn_tu: which is true is there are more than one tax_unit row with is_business = False connected to this donor, and false otherwise
    * female. This is a boolean column which is only applicable to donors with is_person = True and mult_ssn_tu = False. We use the gender from tu_corr if possible, and if  not possible we guess gender based on the name. There is a csv-file of common girl and boy names added to the repo.

    -----------------------------------------------------------------------
    Parameters:
        db_conn: SQLAlchemy db-connection
            An active connection to the database

    -------------------------------------------------------------------------
    Returns:
        d_corr: pd.DataFrame
            filtered and preprosessed donors

        ds_corr: pd.DataFrame
            filtered and preprosessed donations

        tu_corr: pd.DataFrame
            filtered and and preprosessed tax units

        donor_map: pd.DataFrame
            contains the mapping between the merged donors

    """
    # Get all donors with at least one donation
    query = f"""
            SELECT 
                d.ID as 'Donor_ID', 
                d.date_registered, 
                d.name_ID, 
                d.has_password,
                d.is_person,
                d.is_anon,
                d.Meta_owner_ID,
                d.newsletter
            FROM v_Donors_anon d
            INNER JOIN Donations ds on d.ID = ds.Donor_ID
            GROUP BY 
                d.ID, 
                d.date_registered, 
                d.name_ID, 
                d.has_password,
                d.is_person,
                d.is_anon,
                d.Meta_owner_ID, 
                d.newsletter
            """
    d_raw = pd.read_sql(query, db_conn)
    d = d_raw.copy()

    # Get all donations from non-test donors
    query = """
        SELECT 
            ds.* 
        FROM Donations ds
        """
    ds_raw = pd.read_sql(query, db_conn)
    ds_raw = ds_raw.merge(d[["Donor_ID"]], how="inner", on="Donor_ID")
    ds = ds_raw.copy()

    # Get all tax_units from non-test donors
    query = f"""
        SELECT 
            tu.* 
        FROM v_Tax_unit_anon tu
    """
    tu_raw = pd.read_sql(query, db_conn)
    tu_raw = tu_raw.merge(d[["Donor_ID"]], how="inner", on="Donor_ID")
    tu = tu_raw.copy()

    donor_map = pd.DataFrame(columns=["new_donor_id", "old_donor_id"])

    # All anonymous donors get same name_ID
    d.loc[d.is_anon == True, "name_ID"] = d.name_ID.max() + 1

    # Find and merge donors with same first and last name
    d_grouped = d[["Donor_ID", "name_ID"]].groupby(by="name_ID").count()
    dups_count = d_grouped[d_grouped.Donor_ID > 1].reset_index()
    dups_name = dups_count[["name_ID"]].merge(d, how="inner", on="name_ID")

    d_corr, ds_corr, tu_corr, donor_map = merge_donors(
        "name_ID", dups_name, d, ds, tu, donor_map
    )

    # Find and merge donors with same ssn
    query = f"SELECT * FROM Tax_unit"
    tu_ssn = pd.read_sql(query, db_conn)
    tu_ssn = d_corr[["Donor_ID"]].merge(tu_ssn, how="inner", on="Donor_ID")

    count_ssn = tu_ssn[["ID", "ssn"]].groupby("ssn").count()
    count_ssn = count_ssn[
        (count_ssn.index != "")
        & (count_ssn["ID"] > 1)
        & (count_ssn.index.str.isnumeric())
    ]
    dups_ssn = tu_ssn[tu_ssn.ssn.isin(count_ssn.index)][["ID", "Donor_ID", "ssn"]]

    # If the same donor has two taxunits with same ssn
    dups_d_ssn = (
        dups_ssn[["Donor_ID", "ssn"]].drop_duplicates().groupby(by="ssn").count()
    )
    dups_d_ssn = dups_d_ssn[dups_d_ssn.Donor_ID == 1].reset_index()
    tu_dups = dups_d_ssn[["ssn"]].merge(tu_ssn, on="ssn", how="inner")
    tu_dups = tu_dups.sort_values(by=["ssn", "ID"])
    old_tu = tu_dups.drop_duplicates(subset=["ssn", "Donor_ID"], keep="first")
    tu_corr = tu_corr[~tu_corr.ID.isin(old_tu["ID"])]

    # For when different donors have same ssn
    dups_ssn = dups_ssn.rename(columns={"ID": "tu_ID"})
    d_corr, ds_corr, tu_corr, donor_map = merge_donors(
        "ssn", dups_ssn, d_corr, ds_corr, tu_corr, donor_map
    )

    d_corr = set_date_registered_as_first_ds(d_corr, ds_corr)

    # Transform to boolean columns
    d_corr = d_corr.astype(
        {"has_password": bool, "is_person": bool, "is_anon": bool, "newsletter": bool}
    )
    tu_corr = tu_corr.astype({"is_business": bool})

    # Add flag for whether donor has a registered business
    tu_corr_business = tu_corr[tu_corr.is_business]
    d_corr["has_business_tu"] = d_corr.Donor_ID.isin(tu_corr_business.Donor_ID)

    # Add flag for whether donor has registered multiple ssn-numbers
    tu_corr_p = tu_corr[~tu_corr.is_business]
    num_tu_p = (
        tu_corr_p[["ID", "Donor_ID"]]
        .drop_duplicates()
        .groupby("Donor_ID")
        .count()
        .sort_values(by="ID", ascending=False)
    )
    mult_tu_p = num_tu_p[num_tu_p.ID > 1].index
    d_corr["mult_ssn_tu"] = d_corr.Donor_ID.isin(mult_tu_p)

    # Add flag for whether donor is classified as recurring
    rec_df = is_recurring(
        d_corr["Donor_ID"].values.tolist(),
        ds_corr[["Donor_ID", "Timestamp_confirmed", "Payment_ID"]],
        pd.Timestamp.now(),
    )
    d_corr = d_corr.merge(rec_df, how="left", on="Donor_ID")

    # Add a flag for whether donation is from a business
    query = f"""
        SELECT
            c.KID as 'KID_fordeling',
            c.Tax_unit_ID
        FROM
            Combining_table c
    """
    c_table = pd.read_sql(query, db_conn).drop_duplicates()
    ds_corr = ds_corr.merge(c_table, how="left", on="KID_fordeling")
    ds_corr["from_business"] = ds_corr.Tax_unit_ID.isin(tu_corr_business.ID)
    ds_corr.drop(["Tax_unit_ID"], axis=1, inplace=True)

    check_for_duplicates(d_corr, ds_corr, tu_corr)
    return d_corr, ds_corr, tu_corr, donor_map


def get_preprocessed_data(db_conn):
    """
    See more documentation in Data analysis documentation Google doc  https://docs.google.com/document/d/12GaFIQO7vWYqfqWGpAt7MmugmfwhMc5-nx_11wYU3g4/edit#


    # Description
    This function is meant to be run before any data analysis.
    This function will read and clean the data from the v_Donors_anon, v_Tax_unit_anon views and the Donations table.

    ## NB
    * These changes are not done in the data base, and only affect the data analysis in python
    * Important to note that all donors without registered donations in the database are filtered out
    * Any test donors are filtered out in the v_Donors_anon view itself
    * Weakness: In this preprocessing of donors, donations and tax_units, we make the assumption that any donor account with the same first and last name belong to the same person. This is a weakness in the processing, since there could be different persons with the same first and last name.
    However, with our current number of donors, we view the benefit of merging greater than the possible disadvantages

    ## Background
    Some donors will create several different donor accounts over the years. Ie. They may use different emails, but still register with the same first and last name or ssn. To make the data analysis more representative of reality, we want to merge the donors accounts we believe belong to the same person.

    ### Merging duplicates on first and last name
    * Donor accounts without names, only whitespaces as names or only a single word as a name will not be matched
    * We choose to keep only the donor with the most recent donation (aka most_recent_donor) for each group of donors with same first and last name. This means that we transfer all donations to this donor, and filter out the other duplicates from the donor dataframe.
    * We only keep the tax_unit-rows from most_recent_donor

    ### Merging duplicates on ssn
    * If one donor has several tax_units with identical ssn's we choose the most recent tax_unit, and remove the duplicate
    * We choose to keep only the donor with the most recent donation (aka most_recent_donor) for each group of donors with same ssn. This means that we transfer all donations to this donor, and filter out the other duplicates from the donor dataframe.
    * We only keep the tax_unit-rows from most_recent_donor

    ### Setting date_registered as the timestamp of the first donation
    * The date_registered column does not always match the timestamp of the first donation. For data analysis purposes, the date_registered column is changed such that it always matches the first registered donation for this donor.


    ### Adding columns with metadata to d_corr
    We add the columns
    * has_business_tu: which is true if the donor has at least one tax_unit with is_business = True, and false otherwise
    * mult_ssn_tu: which is true is there are more than one tax_unit row with is_business = False connected to this donor, and false otherwise
    * female. This is a boolean column which is only applicable to donors with is_person = True and mult_ssn_tu = False. We use the gender from tu_corr if possible, and if  not possible we guess gender based on the name. There is a csv-file of common girl and boy names added to the repo.

    -----------------------------------------------------------------------
    Parameters:
        db_conn: SQLAlchemy db-connection
            An active connection to the database

    -----------------------------------------------------------------------
    Returns:
        d_corr: pd.DataFrame
            filtered and preprosessed donors

        ds_corr: pd.DataFrame
            filtered and preprosessed donations

        tu_corr: pd.DataFrame
            filtered and and preprosessed tax units

        donor_map: pd.DataFrame
            contains the mapping between the merged donors

    """
    # Do all anonymized preprocessing
    d_corr, ds_corr, tu_corr, donor_map = get_preprocessed_data_anon(db_conn)

    # All preprocessing that requires access to non-anonymized data
    # Find gender and add to donor dataframe
    d_corr = add_gender(d_corr.copy(), tu_corr.copy(), db_conn)

    check_for_duplicates(d_corr, ds_corr, tu_corr)

    return d_corr, ds_corr, tu_corr, donor_map


def set_date_registered_as_first_ds(d_corr, ds_corr):
    """
    -----------------------------------------------------------------------
    Parameters:
        d_corr: pd.DataFrame
            DataFrame with at least columns Donor_ID and date_registered

        ds_corr: pd.DataFrame
            DataFrame with at least columns ID, Donor_ID, and Timestamp_confirmed


    ------------------------------------------------------------------------
    Returns:
        d_corr: pd.DataFrame
            Same as input dataframe d, where date_registered is set as
            the earliest Timestamp_confirmed from ds_corr
    """
    first_ds = ds_corr[["Donor_ID", "Timestamp_confirmed"]].groupby("Donor_ID").min()
    d_corr = d_corr.merge(first_ds, how="left", on="Donor_ID")
    d_corr.rename(columns={"date_registered": "date_registered_old"}, inplace=True)
    d_corr.rename(
        columns={
            "Timestamp_confirmed": "date_registered",
        },
        inplace=True,
    )
    d_corr.drop(["name_ID", "date_registered_old"], axis=1, inplace=True)
    return d_corr


def merge_donors(var, dups, d_corr, ds_corr, tu_corr, donor_map):
    """
    See the docstring of get_preprossed_data_anon() for more details
    -------------------------------------------------------------
    Parameters:
        var: string
            the variable to find duplicates and merge donors based on
            can be either ssn or name_ID

        dups: pd.DataFrame
            Containing all the duplicate donors, at least columns var and Donor_ID

        d_corr: pd.DataFrame
            donors

        ds_corr: pd.DataFrame
            donations

        tu_corr: pd.DataFrame
           tax units

        donor_map: pd.DataFrame
            contains the mapping between the merged donors

    ------------------------------------------------------------
    Returns:
        d_corr: pd.DataFrame
            filtered and preprosessed donors

        ds_corr: pd.DataFrame
            filtered and preprosessed donations

        tu_corr: pd.DataFrame
            filtered and and preprosessed tax units

        donor_map: pd.DataFrame
            contains the mapping between the merged donors
    """
    ds_dups = dups.merge(ds_corr, how="inner", on="Donor_ID")
    most_recent = ds_dups.groupby(by=[var]).agg({"Timestamp_confirmed": ["max"]})
    most_recent.columns = most_recent.columns.droplevel(0)
    most_recent.rename(columns={"max": "Timestamp_confirmed"}, inplace=True)
    most_recent.reset_index(inplace=True)

    most_recent_d = ds_dups.merge(
        most_recent, how="inner", on=[var, "Timestamp_confirmed"]
    )
    most_recent_d = most_recent_d.sort_values(by=[var, "Timestamp_confirmed", "ID"])
    most_recent_d = most_recent_d.drop_duplicates(
        subset=[var, "Timestamp_confirmed"], keep="last"
    )

    most_recent_d = most_recent_d[["Donor_ID", var]].drop_duplicates(keep="last")
    most_recent_d.rename(columns={"Donor_ID": "most_recent_id"}, inplace=True)
    most_recent_d = most_recent_d.merge(dups[[var, "Donor_ID"]], how="inner", on=var)

    # Remove most recent donor from the dataframe, since only need to change the other duplicates
    most_recent_d = most_recent_d[
        most_recent_d.most_recent_id != most_recent_d.Donor_ID
    ]

    # Create a dict that maps all donors that are merged
    donor_map = pd.concat(
        [
            donor_map,
            most_recent_d[["most_recent_id", "Donor_ID"]].rename(
                columns={"most_recent_id": "new_donor_id", "Donor_ID": "old_donor_id"}
            ),
        ]
    )

    # Transfer all donations to the most recent donor
    ds_corr = ds_corr.merge(most_recent_d, how="left", on="Donor_ID")
    ds_corr.loc[ds_corr.most_recent_id.notnull(), "Donor_ID"] = ds_corr.most_recent_id
    ds_corr.drop(["most_recent_id", var], axis=1, inplace=True)

    # Remove all other donors than most_recent_donor from tax_unit dataframe
    tu_corr = tu_corr[~tu_corr.Donor_ID.isin(donor_map.old_donor_id)]

    # Set correct data-type for birthdate
    tu_corr = tu_corr.astype({"birthdate": "datetime64[ns]"})

    # Remove all other donors than most_recent_donor from donor-dataframe
    d_corr = d_corr[~d_corr.Donor_ID.isin(donor_map.old_donor_id)]

    return d_corr, ds_corr, tu_corr, donor_map


def add_gender(d, tu, db_conn):
    """
    -----------------------------------------------------------------------
    Parameters:
        d: pd.DataFrame
            DataFrame with at least columns Donor_ID, mult_ssn_tu and is_person

        tu: pd.DataFrame
            DataFrame with at least columns ID, Donor_ID, is_business and gender

        db_conn: SQLAlchemy db-connection


    ------------------------------------------------------------------------
    Returns:
        d: pd.DataFrame
            Same as input dataframe d, with an extra column female
            The boolean column female indicates whether the donor is female or not
            based on ssn (if available) and first name
    """
    # Gendered names
    gender_df = pd.read_csv("../GenderedNames.csv")
    gender_df["Guttenavn"] = gender_df["Guttenavn"].str.strip().str.lower()
    gender_df["Jentenavn"] = gender_df["Jentenavn"].str.strip().str.lower()

    # All donors
    query = f"SELECT d.ID, d.full_name FROM Donors d where d.full_name is not NULL and not d.full_name=''"
    d_db = pd.read_sql(query, db_conn)
    d_db["first_name"] = d_db.full_name.str.split().str[0]
    d_db["first_name"] = d_db.first_name.str.split("-").str[0].str.strip().str.lower()

    # Find gender for all donors
    d_db.loc[d_db.first_name.isin(gender_df.Jentenavn), "female_name"] = True
    d_db.loc[d_db.first_name.isin(gender_df.Guttenavn), "female_name"] = False
    d_db.rename(columns={"ID": "Donor_ID"}, inplace=True)

    # Find gender for input donors based on names
    # only donors who are individual people can have gender
    ind_person = d[(d.mult_ssn_tu == False) & (d.is_person == True)]
    ind_person = ind_person.merge(
        d_db[["Donor_ID", "female_name"]], how="left", on="Donor_ID"
    )

    # Gender based on ssn
    tu_gender = tu[tu.is_business == 0 & tu.gender.notnull()]
    tu_gender.loc[:, "female_ssn"] = tu_gender.gender == "F"
    ind_person = ind_person.merge(
        tu_gender[["Donor_ID", "female_ssn"]], how="left", on="Donor_ID"
    )

    # Use the gender from ssn as default as it is more secure
    # when we don't know the gender from ssn, use the gender from name
    ind_person["female"] = ind_person.female_ssn
    ind_person.loc[
        ind_person.female.isnull() & ind_person.female_name.notnull(), "female"
    ] = ind_person.female_name

    # merge this new info into input dataframe
    d = d.merge(ind_person[["Donor_ID", "female"]], how="left", on="Donor_ID")

    return d


def is_recurring(d_ids, donations, timestamp):
    """
    Checks if the donors in d_ids were recurring donors at the specified timestamp, and whether they were recurring due to an agreement or not.

    Recurring donors are defined as someone who satisfies one or both of these conditions:

        Has donated at least once during the past 35 days with payment method AvtaleGiro, Vipps recurring or Paypal.
        OR
        Has donated at least once during the past 35 days, and had at least 2 donations in the 65 days previous to that.
        Of these donations there should be at least one donation more than 20 days earlier than the most recent donation,
        and at least one other donation more than 20 days even earlier.
        Ie. Donation 1 <-20days-> Donation 2 <-20 days -> Donation 3.

        When a donor donates the third donation, donation 1 and 2 also count as recurring donations.
        Therefore, we will look both backwards and forwards in time when checking if a donor was a recurring donor at timestamp.

    -----------------------------------------------------------------------
    Parameters:
        d_ids: list
            A list of containing all the donor ids whose recurring status are to be determined

        donations: pd.DataFrame
            All donations relevant for determining the recurring status of d_ids.
            Ie. at least all donations within last 101 days for donors in d_ids list
            Columns Donor_ID, Timestamp_confirmed and Payment_ID

        timestamp: pd.Timestamp
            The point in time for which to determine the recurring status of donors in the d_ids list


    ---------------------------------------------------------------------------
    Returns:
        rec_donor_df: pd.DataFrame
            With columns Donor_ID, is_recurring, has_agreement.
            All donors from input list d_ids and their recurring donor status at timestamp

    """

    # Extract donations from relevant donors
    donations = donations[donations.Donor_ID.isin(d_ids)]

    # Extract donations 101 days back in time from timestamp and 65 days forward in time from timestamp
    donations = donations[
        (donations.Timestamp_confirmed >= timestamp - pd.Timedelta(days=101))
        & (donations.Timestamp_confirmed <= timestamp + pd.Timedelta(days=65))
    ]

    # Extract donations 35 days back in time from timestamp
    donations_35 = donations[
        (donations.Timestamp_confirmed >= timestamp - pd.Timedelta(days=35))
        & (donations.Timestamp_confirmed <= timestamp)
    ]

    # Get all donors that have not donated in the last 35 days
    non_rec_d_ids = [
        donor_id for donor_id in d_ids if donor_id not in donations_35.Donor_ID.values
    ]

    # Get all donors that have donated during the last 35 days with Vipps recurring, AvtaleGiro or PayPal
    agreement_rec_d_ids = donations_35[
        donations_35.Payment_ID.isin([3, 7, 8])
    ].Donor_ID.unique()

    non_agreement_rec_d_ids = []

    remaining_d_ids = list(set(d_ids) - set(non_rec_d_ids) - set(agreement_rec_d_ids))

    for donor_id in remaining_d_ids:
        """
        A refers to last donation before the timestamp
        B refers to a donation that is at least 20 days before donation A or 20 days after donation A
        C refers to a donation that is at least:
            20 days before the earliest of donation A and donation B
            or
            20 days after the latest of donation A and donation B

        If A, B and C are all found, the donor is a recurring donor at the time of the specified timestamp.
        """
        donor_donations = donations[donations.Donor_ID == donor_id]
        donation_A_timestamp = donor_donations[
            donor_donations.Timestamp_confirmed <= timestamp
        ].Timestamp_confirmed.max()
        # Get all donations from donor that are at least 20 days prior to or after donation A
        donations_20_days_prior_A = donor_donations[
            donor_donations.Timestamp_confirmed
            <= donation_A_timestamp - pd.Timedelta(days=20)
        ]
        donations_20_days_after_A = donor_donations[
            donor_donations.Timestamp_confirmed
            >= donation_A_timestamp + pd.Timedelta(days=20)
        ]

        if donations_20_days_prior_A.empty and donations_20_days_after_A.empty:
            # There is no donation at least 20 days before or after donation A
            continue

        if not donations_20_days_prior_A.empty:
            # Only checking backwards in time
            donation_B_timestamp = donations_20_days_prior_A.Timestamp_confirmed.max()
            donations_20_days_prior_B = donations_20_days_prior_A[
                donations_20_days_prior_A.Timestamp_confirmed
                <= donation_B_timestamp - pd.Timedelta(days=20)
            ]
            if not donations_20_days_prior_B.empty:
                # There is a donation at least 20 days before donation B
                donation_C_timestamp = (
                    donations_20_days_prior_B.Timestamp_confirmed.max()
                )
                if (donation_A_timestamp - donation_C_timestamp).days <= 65:
                    # The donation A, B and C were within 65 days of each other
                    non_agreement_rec_d_ids = np.append(
                        non_agreement_rec_d_ids, donor_id
                    )
                    continue

        if not donations_20_days_after_A.empty:
            # Only checking forwards in time
            donation_B_timestamp = donations_20_days_after_A.Timestamp_confirmed.min()
            donations_20_days_after_B = donations_20_days_after_A[
                donations_20_days_after_A.Timestamp_confirmed
                >= donation_B_timestamp + pd.Timedelta(days=20)
            ]
            if not donations_20_days_after_B.empty:
                # There is a donation at least 20 days after donation B
                donation_C_timestamp = (
                    donations_20_days_after_B.Timestamp_confirmed.min()
                )
                if (donation_C_timestamp - donation_A_timestamp).days <= 65:
                    # The donation A, B and C were within 65 days of each other
                    non_agreement_rec_d_ids = np.append(
                        non_agreement_rec_d_ids, donor_id
                    )
                    continue

        if donations_20_days_after_A.empty or donations_20_days_prior_A.empty:
            continue

        # There are donations both before and after donation A, but no direction satisfies the requirements by itself
        donation_B_timestamp = donations_20_days_after_A.Timestamp_confirmed.min()
        donation_C_timestamp = donations_20_days_prior_A.Timestamp_confirmed.max()

        if (donation_B_timestamp - donation_C_timestamp).days <= 65:
            # The donation A, B and C were within 65 days of each other
            non_agreement_rec_d_ids = np.append(non_agreement_rec_d_ids, donor_id)

    rec_d_ids = np.append(agreement_rec_d_ids, non_agreement_rec_d_ids)

    # Create a dataframe with Donor_ID, is_recurring and has_agreement columns and incldue all donors
    rec_donor_df = pd.DataFrame(
        {"Donor_ID": d_ids, "is_recurring": False, "has_agreement": False}
    )
    rec_donor_df.loc[rec_donor_df.Donor_ID.isin(rec_d_ids), "is_recurring"] = True
    rec_donor_df.loc[
        rec_donor_df.Donor_ID.isin(agreement_rec_d_ids), "has_agreement"
    ] = True

    return rec_donor_df


def get_direct_GE_ds_percentages(db_conn):
    query = """
        SELECT
            c.KID as 'KID_fordeling',
            dist.percentage_share as 'GE_percent'
        FROM
            Combining_table c
        INNER JOIN Distribution dist ON dist.ID = c.Distribution_ID
        WHERE dist.OrgId = 11  
    """
    direct_GE = pd.read_sql(query, db_conn)
    return direct_GE


def remove_direct_GE_donations(donations, db_conn):
    direct_GE = get_direct_GE_ds_percentages(db_conn)
    donations_orgs = donations.merge(direct_GE, how="left", on="KID_fordeling")
    donations_orgs["GE_percent"] = donations_orgs.GE_percent.fillna(0)
    donations_orgs = donations_orgs[donations_orgs.GE_percent != 100]
    donations_orgs["Sum_confirmed"] = (
        donations_orgs["Sum_confirmed"] * 0.01 * (100 - donations_orgs["GE_percent"])
    )
    donations_orgs.drop(["GE_percent"], axis=1, inplace=True)
    return donations_orgs


def extract_direct_GE_donations(donations, db_conn):
    direct_GE = get_direct_GE_ds_percentages(db_conn)
    donations_GE = donations.merge(direct_GE, how="left", on="KID_fordeling")
    donations_GE["GE_percent"] = donations_GE.GE_percent.fillna(0)
    donations_GE = donations_GE[donations_GE.GE_percent != 0]
    donations_GE["Sum_confirmed"] = (
        donations_GE["Sum_confirmed"] * 0.01 * (donations_GE["GE_percent"])
    )
    donations_GE.drop(["GE_percent"], axis=1, inplace=True)
    return donations_GE


def remove_anonymous_donations(donations, donors):
    non_anon_ds = donations.merge(
        donors[["Donor_ID", "is_anon"]], how="left", on="Donor_ID"
    )
    non_anon_ds = non_anon_ds[non_anon_ds.is_anon == False]
    non_anon_ds.drop(["is_anon"], axis=1, inplace=True)
    return non_anon_ds
