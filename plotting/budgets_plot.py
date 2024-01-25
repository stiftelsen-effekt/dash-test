import plotly.graph_objects as go
import numpy as np
import pandas as pd

level2x = {
    1: 0.01,
    2: 0.4,
    3: 0.6,
    4: 0.99
}

HEIGHT = 400
PAD = 15
NUM_LEVELS = 4

def map_unity(num): #Map number from 0-1 to 0.001-0.999 to comply with sankey diagram coordinates
    #return 0.001 + num*(0.999-0.001)
    return 0.01 + num*(0.99-0.01)

class Node():
    def __init__(self, id, name, level, value=None):
        self.id = id
        self.name = name
        self.level = level
        self.value = value
    
    def total_value_on_level(self, budget):
        return sum([node.value for node in budget.nodes if node.level==self.level])
    
    def index_on_level(self, budget):
        return next(i for i,node in enumerate(budget.nodes_on_level(self.level)) if node==self)
    
    def values_above_node(self, budget):
        nodes_on_level = budget.nodes_on_level(level=self.level)
        index_on_level = next(i for i,node in enumerate(nodes_on_level) if node==self)
        #return sum([n.value for n in nodes_on_level if n.value>self.value])
        return sum([n.value for n in nodes_on_level[:index_on_level]])
    
    def get_x(self):
        return map_unity((self.level-1)/(NUM_LEVELS-1))
    
    def get_y(self, budget):
        max_level_value = max([budget.total_value_on_level(level) for level in range(0,NUM_LEVELS+1)])
        #total_value = self.total_value_on_level(budget=budget)
        values_above = self.values_above_node(budget=budget)
        # nodes_on_level = [node for node in budget.nodes if node.level==self.level]
        # index_on_level = next(i for i,node in enumerate(nodes_on_level) if node==self)
        index_on_level = self.index_on_level(budget)
        #total_level_pads = len(budget.nodes_on_level(self.level)) - 1
        max_level_pads = budget.level_with_max_nodes() - 1
        #max_level_pads = max([len(budget.nodes_on_level(level)) for level in range(1,NUM_LEVELS+1) if budget.total_value_on_level(level)>0.95*max_level_value])
        y_nopad = (1/max_level_value)*(0.5*self.value + values_above)
        # return map_unity((1/max_level_value)*(0.5*self.value + values_above) + index_on_level*(PAD/HEIGHT))
        return y_nopad*(1 - max_level_pads*PAD/HEIGHT) + index_on_level*(PAD/HEIGHT)
        
class Link():
    def __init__(self, source, target, value, levels):
        self.source= source
        self.target = target
        self.value = value
        self.levels = levels

class Budget():
    def __init__(self, year, links) -> None:
        self.year = year
        self.links = links
        self.nodes = self.make_nodes()

    def node_id_by_name(self, name):
        return next(node.id for node in self.nodes if node.name==name)
    
    def nodes_on_level(self, level):
        return [node for node in self.nodes if node.level==level]
    
    def level_with_max_nodes(self):
        return max([len(self.nodes_on_level(level)) for level in range(1,NUM_LEVELS+1)])
    
    def total_value_on_level(self, level):
        return sum([node.value for node in self.nodes if node.level==level])
    
    def make_nodes(self):
        links_df = pd.DataFrame(data={
            'Source': [link.source for link in self.links],
            'Target': [link.target for link in self.links],
            'Value':  [link.value for link in self.links],
        })

        node_names = list(pd.unique(links_df[['Source', 'Target']].values.ravel('K')))
        # #unique_source_target = list(pd.unique(links_df[['Source', 'Target']].values.ravel('K')))
        # mapping_dict = {k: v for v, k in enumerate(node_names)}
        # links_df['Source'] = links_df['Source'].map(mapping_dict)
        # links_df['Target'] = links_df['Target'].map(mapping_dict)
        # links_dict = links_df.to_dict(orient='list')

        node2level = { #Mapping from node to level/column
            **{link.source: link.levels[0] for link in self.links},
            **{link.target: link.levels[1] for link in self.links}
        }
        nodes = [None]*len(node_names)
        for i,node_name in enumerate(node_names):
            nodes[i] = Node(
                id = i,
                name = node_name,
                level = node2level[node_name],
                value = sum([link.value for link in self.links if any([link.source==node_name and node2level[node_name]==1,link.target==node_name])])
            )
        #levels = np.array([node2level[key] for key in unique_source_target]) #List of levels
        #index_on_level = np.array([i-list(levels).index(node2level[node_name]) for i,node_name in enumerate(unique_source_target)]) #Index of node in relation to other nodes on same level
        #node_values = np.array([sum([link.value for link in self.links if any([link.source==node and node2level[node]==1,link.target==node])]) for node in unique_source_target]) #Value of node
        
        return nodes
    
    # def total_value_on_level(self, level):
    #     return sum([node.value for node in self.nodes if node.level==level])
    
    # def values_above_node(self, level, node):
    #     nodes_on_level = [node for node in self.nodes if node.level==level]
    #     return sum([n.value for n in nodes_on_level if n.value>node.value])

budget_2016 = Budget(
    year=2016,
    links=[
        Link("Donasjoner til drift", "Inntekter", 146_870, (1, 2)),
        Link("Donasjoner til formål", "Inntekter", 46_782, (1, 2)),
        Link("Inntekter", "Ordinært resultat", 119_492, (2, 3)),
        Link("Inntekter", "Utgifter", 74_161, (2, 3)),
        Link("Utgifter", "Lønn", 57_744, (3, 4)),
        Link("Utgifter", "Arbeidsgiveravgift", 8_280, (3, 4)),
        Link("Utgifter", "Nettside", 1_919, (3, 4)),
        Link("Utgifter", "Reisekostnader", 1_587, (3, 4)),
        Link("Utgifter", "Personalkostnad", 1_532, (3, 4)),
        Link("Utgifter", "Diverse driftskostnader", 970, (3, 4)),
        Link("Utgifter", "Annen personalkostnad", 542, (3, 4)),
        Link("Utgifter", "Telefon, porto og epost", 542, (3, 4)),
        Link("Utgifter", "Reklame/annonser", 542, (3, 4)),
        Link("Utgifter", "Finanskostnader", 436, (3, 4))
    ]
)

budget_2017 = Budget(
    year = 2017,
    links = [
        Link("Donasjoner til formål", "Inntekter", 1_810_231, (1,2)),
        Link("Donasjoner til drift", "Inntekter", 56_969, (1,2)),
        Link("Finansinntekter", "Inntekter", 640, (1,2)),
        Link("Inntekter", "Ordinært resultat", 373_804, (2,3)),
        Link("Inntekter", "Utgifter", 1_494_036, (2,3)),
        Link("Utgifter", "Overføring til formål", 1_433_289, (3,4)),
        Link("Utgifter", "Regnskap og revisjon", 12_688, (3,4)),
        Link("Utgifter", "Reisekostnader", 23_603, (3,4)),
        Link("Utgifter", "Profilering", 3_355, (3,4)),
        Link("Utgifter", "Nettside", 4_362, (3,4)),
        Link("Utgifter", "Bank og transaksjonsgebyrer", 8_614, (3,4)),
        Link("Utgifter", "Annet", 4_810, (3,4)),
        Link("Utgifter", "Lønn og personalkostnader", 3_316, (3,4))
    ]
)

budget_2018 = Budget(
    year = 2018,
    links = [
        Link("Donasjoner til formål", "Inntekter", 1_787_198, (1,2)),
        Link("Donasjoner til drift", "Inntekter", 68_455, (1,2)),
        Link("Finansinntekter", "Inntekter", 4_432, (1,2)),
        Link("Inntekter", "Utgifter", 1_612_646, (2,3)),
        Link("Inntekter", "Ordinært resultat", 239_944, (2,3)),
        Link("Inntekter", "Valutatap", 7_495, (2,3)),
        Link("Utgifter", "Overføring til formål", 1_543_672, (3,4)),
        Link("Utgifter", "Nettside", 23_502, (3,4)),
        Link("Utgifter", "Regnskap og revisjon", 20_000, (3,4)),
        Link("Utgifter", "Bank og transaksjonsgebyrer", 10_426, (3,4)),
        Link("Utgifter", "Reisekostnader", 9_037, (3,4)),
        Link("Utgifter", "Annet", 6_010, (3,4))
    ]
)

budget_2019 = Budget(
    year = 2019,
    links = [
        Link("Donasjoner til formål", "Inntekter", 2_353_327, (1,2)),
        Link("Ordinært resultat", "Inntekter", 234_184, (1,2)),
        Link("Offentlige tilskudd", "Inntekter", 105_648, (1,2)),
        Link("Donasjoner til drift", "Inntekter", 30_583, (1,2)),
        Link("Finansinntekter", "Inntekter", 2_125, (1,2)),
        Link("Inntekter", "Utgifter", 2_715_470, (2,3)),
        Link("Inntekter", "Valutatap", 10_398, (2,3)),
        Link("Utgifter", "Overføring til formål", 2_654_583, (3,4)),
        Link("Utgifter", "Profilering", 21_061, (3,4)),
        Link("Utgifter", "Regnskap og revisjon", 12_552, (3,4)),
        Link("Utgifter", "Bank og transaksjonsgebyrer", 12_350, (3,4)),
        Link("Utgifter", "Annet", 9_628, (3,4)),
        Link("Utgifter", "Reisekostnader", 2_876, (3,4)),
        Link("Utgifter", "Nettside", 2_420, (3,4)),
    ]
)

budget_2020 = Budget(
    year = 2020,
    links = [
        Link("Donasjoner til formål", "Inntekter", 6_914_137, (1,2)),
        Link("Offentlige tilskudd", "Inntekter", 175_927, (1,2)),
        Link("Finansinntekter", "Inntekter", 33_549, (1,2)),
        Link("Donasjoner til drift", "Inntekter", 7_571, (1,2)),
        Link("Inntekter", "Utgifter", 4_885_563, (2,3)),
        Link("Inntekter","Ordinært resultat", 2_237_112, (2,3)),
        Link("Inntekter", "Valutatap", 10_398, (2,3)),
        Link("Utgifter", "Tilskudd anbefalte org.", 4_689_672, (3,4)),
        Link("Utgifter", "Reklame/annonser", 166_711, (3,4)),
        Link("Utgifter", "Regnskap og revisjon", 14_000, (3,4)),
        Link("Utgifter", "Forsikringer", 5_690, (3,4)),
        Link("Utgifter", "Diverse driftskostnader", 4_640, (3,4)),
        Link("Utgifter", "Bank og transaksjonsgebyrer", 3_420+65+1, (3,4)),
        Link("Utgifter", "Nettside", 1_365, (3,4))
    ]
)

budget_2021 = Budget(
    year = 2021,
    links = [
        Link('Donasjoner til drift', "Inntekter", 895_700, (1,2)),
        Link('Offentlige tilskudd', "Inntekter", 390_845, (1,2)),
        Link('Driftstøtte CEA', "Inntekter", 383_952, (1,2)),
        Link('Andre tilskudd', "Inntekter", 70_000, (1,2)),
        Link("Finansinntekter", "Inntekter", 644+116, (1,2)),
        Link('Annen inntekt', "Inntekter", 731, (1,2)),
        Link("Inntekter", "Utgifter", 895_700+390_845+383_952+70_000+644+116+731-332_882, (2,3)),
        Link("Inntekter","Ordinært resultat", 332_882, (2,3)),
        Link('Utgifter','Personalkostnader', 806_780, (3,4)),
        Link('Utgifter','Fremmed tjeneste',  422_938, (3,4)),
        Link('Utgifter','Reklamekostnad o.l.',  78_842, (3,4)),
        Link('Utgifter','Bank- og transaksjonsgebyrer', 27_540, (3,4)),
        Link('Utgifter','Driftsmaterialer som ikke aktiveres', 20_107, (3,4)),
        Link('Utgifter','Annen driftskostnad', 19_452, (3,4)),
        Link('Utgifter','Kostnad lokaler', 16_000, (3,4)),
        Link("Utgifter", "Finansutgifter", 10_341+134, (3,4)),
        Link('Utgifter','Forsikringspremie', 7_568, (3,4)),
        Link('Utgifter','Kostnad og godtgjørelse',  6_473, (3,4)),
        Link('Utgifter','Møter, kontorutstyr o.l.',  2_647, (3,4))
    ]
)

budget_2022 = Budget(
    year = 2022,
    links = [
        Link('Donasjoner til drift', "Inntekter", 1_892_114, (1,2)),
        Link('Driftstøtte CEA', "Inntekter", 715_744, (1,2)),
        Link('Andre tilskudd', "Inntekter", 256_875, (1,2)),
        Link('Offentlige tilskudd', "Inntekter", 112_571, (1,2)),
        Link('Annen inntekt', "Inntekter", 797, (1,2)),
        Link("Finansinntekter", "Inntekter", 6_873+3_219, (1,2)),
        Link("Inntekter", "Utgifter", 112_571+256_875+715_744+1_892_114+797-323_308, (2,3)),
        Link("Inntekter","Ordinært resultat", 323_308, (2,3)),
        Link('Utgifter','Personalkostnader', 1_530_298, (3,4)),
        Link('Utgifter','Fremmed tjeneste', 574_264, (3,4)),
        Link('Utgifter','Reklamekostnad o.l.', 294_189, (3,4) ),
        Link("Utgifter", "Finansutgifter", 78_339+22_337, (3,4)),
        Link('Utgifter','Driftsmaterialer som ikke aktiveres', 75_882, (3,4)),
        Link('Utgifter','Bank- og transaksjonsgebyrer', 68_730, (3,4) ),
        Link('Utgifter','Kostnad og godtgjørelse', 42_031, (3,4)),
        Link('Utgifter','Kostnad lokaler', 27_500, (3,4)),
        Link('Utgifter','Annen Utgifter', 26_342, (3,4)),
        Link('Utgifter','Forsikringspremie', 10_731, (3,4)),
        Link('Utgifter','Møter, kontorutstyr o.l.', 4_826, (3,4))
    ]
)

budgets_ = [budget_2016, budget_2017, budget_2018, budget_2019, budget_2020, budget_2021, budget_2022]

budgets = {
    2016 : [   #[From, To, Value, (Level_from, Level_to)]
                ["Donasjoner til drift", "Inntekter", 146_870, (1, 2)],
                ["Donasjoner til formål", "Inntekter", 46_782, (1, 2)],

                ["Inntekter", "Ordinært resultat", 119_492, (2, 3)],
                ["Inntekter", "Utgifter", 74_161, (2, 3)],

                ["Utgifter", "Lønn", 57_744, (3, 4)],
                ["Utgifter", "Arbeidsgiveravgift", 8_280, (3, 4)],
                ["Utgifter", "Nettside", 1_919, (3, 4)],
                ["Utgifter", "Reisekostnader", 1_587, (3, 4)],
                ["Utgifter", "Personalkostnad", 1_532, (3, 4)],
                ["Utgifter", "Diverse driftskostnader", 970, (3, 4)],
                ["Utgifter", "Annen personalkostnad", 542, (3, 4)],
                ["Utgifter", "Telefon, porto og epost", 542, (3, 4)],
                ["Utgifter", "Reklame/annonser", 542, (3, 4)],
                ["Utgifter", "Finanskostnader", 436, (3, 4)],
                ],
    2017 : [
                ["Donasjoner til formål", "Inntekter", 1_810_231, (1,2)],
                ["Donasjoner til drift", "Inntekter", 56_969, (1,2)],
                ["Finansinntekter", "Inntekter", 640, (1,2)],

                ["Inntekter", "Ordinært resultat", 373_804, (2,3)],
                ["Inntekter", "Utgifter", 1_494_036, (2,3)],

                ["Utgifter", "Overføring til formål", 1_433_289, (3,4)],
                ["Utgifter", "Regnskap og revisjon", 12_688, (3,4)],
                ["Utgifter", "Reisekostnader", 23_603, (3,4)],
                ["Utgifter", "Profilering", 3_355, (3,4)],
                ["Utgifter", "Nettside", 4_362, (3,4)],
                ["Utgifter", "Bank og transaksjonsgebyrer", 8_614, (3,4)],
                ["Utgifter", "Annet", 4_810, (3,4)],
                ["Utgifter", "Lønn og personalkostnader", 3_316, (3,4)],
                ],
    2018 : [
                ["Donasjoner til formål", "Inntekter", 1_787_198, (1,2)],
                ["Donasjoner til drift", "Inntekter", 68_455, (1,2)],
                ["Finansinntekter", "Inntekter", 4_432, (1,2)],

                ["Inntekter", "Utgifter", 1_612_646, (2,3)],
                ["Inntekter", "Ordinært resultat", 239_944, (2,3)],
                ["Inntekter", "Valutatap", 7_495, (2,3)],

                ["Utgifter", "Overføring til formål", 1_543_672, (3,4)],
                ["Utgifter", "Nettside", 23_502, (3,4)],
                ["Utgifter", "Regnskap og revisjon", 20_000, (3,4)],
                ["Utgifter", "Bank og transaksjonsgebyrer", 10_426, (3,4)],
                ["Utgifter", "Reisekostnader", 9_037, (3,4)],
                ["Utgifter", "Annet", 6_010, (3,4)],
                ],
    2019 : [
                ["Donasjoner til formål", "Inntekter", 2_353_327, (1,2)],
                ["Ordinært resultat", "Inntekter", 234_184, (1,2)],
                ["Offentlige tilskudd", "Inntekter", 105_648, (1,2)],
                ["Donasjoner til drift", "Inntekter", 30_583, (1,2)],
                ["Finansinntekter", "Inntekter", 2_125, (1,2)],

                ["Inntekter", "Utgifter", 2_715_470, (2,3)],
                ["Inntekter", "Valutatap", 10_398, (2,3)],

                ["Utgifter", "Overføring til formål", 2_654_583, (3,4)],
                ["Utgifter", "Profilering", 21_061, (3,4)],
                ["Utgifter", "Regnskap og revisjon", 12_552, (3,4)],
                ["Utgifter", "Bank og transaksjonsgebyrer", 12_350, (3,4)],
                ["Utgifter", "Annet", 9_628, (3,4)],
                ["Utgifter", "Reisekostnader", 2_876, (3,4)],
                ["Utgifter", "Nettside", 2_420, (3,4)],
                ],
    2020 : [
                ["Donasjoner til formål", "Inntekter", 6_914_137, (1,2)],
                ["Offentlige tilskudd", "Inntekter", 175_927, (1,2)],
                ["Finansinntekter", "Inntekter", 33_549, (1,2)],
                ["Donasjoner til drift", "Inntekter", 7_571, (1,2)],

                ["Inntekter", "Utgifter", 4_885_563, (2,3)],
                ["Inntekter","Ordinært resultat", 2_237_112, (2,3)],
                ["Inntekter", "Valutatap", 10_398, (2,3)],

                ["Utgifter", "Tilskudd anbefalte org.", 4_689_672, (3,4)],
                ["Utgifter", "Reklame/annonser", 166_711, (3,4)],
                ["Utgifter", "Regnskap og revisjon", 14_000, (3,4)],
                ["Utgifter", "Forsikringer", 5_690, (3,4)],
                ["Utgifter", "Diverse driftskostnader", 4_640, (3,4)],
                ["Utgifter", "Bank og transaksjonsgebyrer", 3_420+65+1, (3,4)],
                ["Utgifter", "Nettside", 1_365, (3,4)],
                ],
    2021 : [
                ['Donasjoner til drift', "Inntekter", 895_700, (1,2)],
                ['Offentlige tilskudd', "Inntekter", 390_845, (1,2)],
                ['Driftstøtte CEA', "Inntekter", 383_952, (1,2)],
                ['Andre tilskudd', "Inntekter", 70_000, (1,2)],
                ["Finansinntekter", "Inntekter", 644+116, (1,2)],
                ['Annen inntekt', "Inntekter", 731, (1,2)],

                ["Inntekter", "Utgifter", 390_845+70_000+383_952+895_700+731+644+116-332_882, (2,3)],
                ["Inntekter","Ordinært resultat", 332_882, (2,3)],
                
                ['Utgifter','Personalkostnader', 806_780, (3,4)],
                ['Utgifter','Fremmed tjeneste',  422_938, (3,4)],
                ['Utgifter','Reklamekostnad o.l.',  78_842, (3,4)],
                ['Utgifter','Bank- og transaksjonsgebyrer', 27_540, (3,4)],
                ['Utgifter','Driftsmaterialer som ikke aktiveres', 20_107, (3,4)],
                ['Utgifter','Annen driftskostnad', 19_452, (3,4)],
                ['Utgifter','Kostnad lokaler', 16_000, (3,4)],
                ["Utgifter", "Finansutgifter", 10_341+134, (3,4)],
                ['Utgifter','Forsikringspremie', 7_568, (3,4)],
                ['Utgifter','Kostnad og godtgjørelse',  6_473, (3,4)],
                ['Utgifter','Møter, kontorutstyr o.l.',  2_647, (3,4)],
                ],
    2022 : [
                ['Donasjoner til drift', "Inntekter", 1_892_114, (1,2)],
                ['Driftstøtte CEA', "Inntekter", 715_744, (1,2)],
                ['Andre tilskudd', "Inntekter", 256_875, (1,2)],
                ['Offentlige tilskudd', "Inntekter", 112_571, (1,2)],
                ['Annen inntekt', "Inntekter", 797, (1,2)],
                ["Finansinntekter", "Inntekter", 6_873+3_219, (1,2)],

                ["Inntekter", "Utgifter", 112_571+256_875+715_744+1_892_114+797-323_308, (2,3)],
                ["Inntekter","Ordinært resultat", 323_308, (2,3)],
                
                ['Utgifter','Personalkostnader', 1_530_298, (3,4)],
                ['Utgifter','Fremmed tjeneste', 574_264, (3,4)],
                ['Utgifter','Reklamekostnad o.l.', 294_189, (3,4) ],
                ["Utgifter", "Finansutgifter", 78_339+22_337, (3,4)],
                ['Utgifter','Driftsmaterialer som ikke aktiveres', 75_882, (3,4)],
                ['Utgifter','Bank- og transaksjonsgebyrer', 68_730, (3,4) ],
                ['Utgifter','Kostnad og godtgjørelse', 42_031, (3,4)],
                ['Utgifter','Kostnad lokaler', 27_500, (3,4)],
                ['Utgifter','Annen Utgifter', 26_342, (3,4)],
                ['Utgifter','Forsikringspremie', 10_731, (3,4)],
                ['Utgifter','Møter, kontorutstyr o.l.', 4_826, (3,4)],
                ],
}


def plot_sankey(year):
    #relevant_budget = budgets[year]
    relevant_budget = next(budget for budget in budgets_ if budget.year==year)
    #relevant_budget = sorted(budgets[year], key=lambda x: x[2])[::-1]

    # links_df = pd.DataFrame(data={
    #     'Source': [lst[0] for lst in relevant_budget],
    #     'Target': [lst[1] for lst in relevant_budget],
    #     'Value':  [lst[2] for lst in relevant_budget],
    # })
    # unique_source_target = list(pd.unique(links_df[['Source', 'Target']].values.ravel('K')))
    # mapping_dict = {k: v for v, k in enumerate(unique_source_target)}
    # links_df['Source'] = links_df['Source'].map(mapping_dict)
    # links_df['Target'] = links_df['Target'].map(mapping_dict)
    # links_dict = links_df.to_dict(orient='list')

    # relevant_labels = np.unique([lst[0] for lst in relevant_budget]+[lst[1] for lst in relevant_budget])
    # relevant_sources = [np.where(relevant_labels==lst[0])[0][0] for lst in relevant_budget]
    # relevant_targets = [np.where(relevant_labels==lst[1])[0][0] for lst in relevant_budget]
    
    # val_dict = {lst[0]: lst[2] for lst in relevant_budget}
    # val_dict.update({lst[1]: lst[2] for lst in relevant_budget})
    # relevant_values = [val_dict[lbl] for lbl in relevant_labels]

    # val_dict = {lst[0]: sum([row[2] for row in relevant_budget if row[0]==lst[0]]) for lst in relevant_budget}
    # val_dict.update({lst[1]: sum([row[2] for row in relevant_budget if row[1]==lst[1]]) for lst in relevant_budget})
    # relevant_values = [val_dict[lbl] for lbl in relevant_labels]

    #relevant_values = np.array([lst[2] for lst in relevant_budget])[np.unique(relevant_sources)]
    #relevant_values = [np.where(relevant_labels==lst[2])[0][0] for lst in relevant_budget]
    
    # node2level = {**{lst[0]: lst[3][0] for lst in relevant_budget},**{lst[1]: lst[3][1] for lst in relevant_budget}} #Mapping from node to level/column
    # levels = np.array([node2level[key] for key in unique_source_target]) #List of levels
    # index_on_level = np.array([i-list(levels).index(node2level[node_name]) for i,node_name in enumerate(unique_source_target)]) #Index of node in relation to other nodes on same level
    # node_values = np.array([sum([lst[2] for lst in relevant_budget if any([lst[0]==node and node2level[node]==1,lst[1]==node])]) for node in unique_source_target]) #Value of node
    # level_total_values = [sum(np.array(node_values)[levels==node2level[node]]) for node in unique_source_target] #Total sum of all nodes on level of node
    # values_above = [sum([node_values[m] for m,node_m in enumerate(unique_source_target[:n]) if node2level[node_n]==node2level[node_m]]) for n,node_n in enumerate(unique_source_target)]

    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = PAD,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            #label = unique_source_target,
            label = [node.name for node in relevant_budget.nodes],
            #label = [f'{label}: {val:,} kr' for label, val in zip(unique_source_target,node_values)],
            color = "black",
            hovertemplate= '<b>%{label}</b><br>%{value:,} kr<extra></extra>',
            #x = [level2x[node2level[node_name]] for node_name in unique_source_target],
            x = [node.get_x() for node in relevant_budget.nodes],
            #x = [map_unity((node2level[node_name]-1)/3) for node_name in unique_source_target],
            #y = [map_unity(index_on_level[i]/max(levels.count(node2level[node])-1,1)) for i,node in enumerate(unique_source_target)]
            #y = [index_on_level[i]*0.0001 for i,node in enumerate(unique_source_target)]
            #y = [map_unity((1/max(level_total_values))*(0.5*node_values[i] + values_above[i])) for i,node in enumerate(unique_source_target)]
            y = [node.get_y(relevant_budget) for node in relevant_budget.nodes]
        ),
        link = dict(
            # source = links_dict["Source"],
            source = [relevant_budget.node_id_by_name(link.source) for link in relevant_budget.links],
            target = [relevant_budget.node_id_by_name(link.target) for link in relevant_budget.links],
            value =  [link.value for link in relevant_budget.links],
            # target = links_dict["Target"],
            # value = links_dict["Value"],
            #hoverinfo='skip'
            #line = dict(color = "black", width = 0.5),
            color = "lightgrey",
            hovertemplate='<b>%{source.label}-%{target.label}</b><br>%{value:,} kr<extra></extra>'
        ),
        arrangement='fixed',
        orientation='h'
        
    )], 
    layout=dict(
        margin=dict(l=0,r=0,t=0,b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_family="ESKlarheit",
        #width=900,
        height=HEIGHT,
    )
    )
    return fig