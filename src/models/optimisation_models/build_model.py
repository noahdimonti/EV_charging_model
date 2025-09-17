import pyomo.environ as pyo
from src.config import params
from src.models.utils.configs import (
    CPConfig,
    ChargingStrategy
)
from src.models.optimisation_models.assets.grid import Grid
from src.models.optimisation_models.assets.household_load import HouseholdLoad
from src.models.optimisation_models.assets.common_connection_point import CommonConnectionPoint
from src.models.optimisation_models.assets.charging_point import ChargingPoint
from src.models.optimisation_models.assets.electric_vehicle import ElectricVehicle
from src.models.optimisation_models.objectives import EconomicObjective, TechnicalObjective, SocialObjective


class BuildModel:
    def __init__(self,
                 config: CPConfig,
                 charging_strategy: ChargingStrategy,
                 version: str,
                 obj_weights: dict[str, int|float]):
        self.config = config
        self.charging_strategy = charging_strategy
        self.version = version
        self.obj_weights = obj_weights

        self.model = pyo.ConcreteModel(
            name=f'{config.value}_{charging_strategy.value}_{params.num_of_evs}EVs_{self.version}'
        )
        self.assets = {}

        # Validate configuration and charging mode
        CPConfig.validate(self.config)
        ChargingStrategy.validate(self.charging_strategy)

        # Run methods
        self.initialise_sets()
        self.assemble_components()

    def initialise_sets(self):
        self.model.EV_ID = pyo.Set(initialize=[_ for _ in range(params.num_of_evs)])
        self.model.TIME = pyo.Set(initialize=params.timestamps)
        self.model.DAY = pyo.Set(initialize=[_ for _ in params.T_d.keys()])
        self.model.WEEK = pyo.Set(initialize=[_ for _ in params.D_w.keys()])

    def _normalise_cost(self):
        pass

    def define_objective_components(self):
        # Economic objective
        economic_obj = EconomicObjective(self.model)

        investment_cost = (
            economic_obj.investment_cost()
            if self.config.value == 'config_1'
            else economic_obj.investment_cost_linearised()
        )

        economic_cost = (
                investment_cost +
                economic_obj.maintenance_cost() +
                economic_obj.energy_purchase_cost()
        )

        self.model.economic_objective = pyo.Expression(expr=economic_cost)

        # Technical objective
        technical_obj = TechnicalObjective(self.model)

        technical_cost = (
                technical_obj.f_disc() +
                technical_obj.f_peak() +
                technical_obj.f_papr()
        )

        self.model.technical_objective = pyo.Expression(expr=technical_cost)

        # Social objective
        social_obj = SocialObjective(self.model)

        social_cost = (
                social_obj.f_soc() +
                social_obj.f_fair()
        )

        self.model.social_objective = pyo.Expression(expr=social_cost)

        # Normalise objective


        # Total objective
        self.model.obj_function = pyo.Objective(
            expr=(
                    self.obj_weights['economic'] * self.model.economic_objective +
                    self.obj_weights['technical'] * self.model.technical_objective +
                    self.obj_weights['social'] * self.model.social_objective
            ),
            sense=pyo.minimize
        )

    def assemble_components(self):
        # Initialise assets parameters and variables
        self.assets['grid'] = Grid(self.model)
        self.assets['household'] = HouseholdLoad(self.model)
        self.assets['ccp'] = CommonConnectionPoint(self.model)
        self.assets['cp'] = ChargingPoint(self.model, self.config, self.charging_strategy)
        self.assets['ev'] = ElectricVehicle(self.model, self.config,
                                            self.charging_strategy)

        # Initialise constraints
        self.assets['ccp'].initialise_constraints()
        self.assets['cp'].initialise_constraints()
        self.assets['ev'].initialise_constraints()

        # Define objective components
        self.define_objective_components()

    def get_optimisation_model(self):
        return self.model





    # def get_f_star(self):
    #     # Load precomputed f* values
    #     obj_terms = [
    #         'f_star_economic',
    #         'f_star_technical',
    #         'f_star_social'
    #     ]
    #
    #     for term in obj_terms:
    #         filename = f'{params.raw_val_metrics_filename_format}_{params.num_of_evs}EVs_{term}.csv'
    #         filepath = os.path.join(params.f_star_values_folder_path, filename)
    #         df = pd.read_csv(filepath, index_col=0)
    #
    #         # Extract the 'objective_value' row and transpose to become a column
    #         extracted = df.loc[['objective_value']].transpose()
    #         extracted.columns = [term]  # Rename the column to reflect the objective term
    #
    #         # Convert to dict with config as key and objective value as float, and assign to f_star_values attribute
    #         _, _, term_name = term.split('_')  # convert term from 'f_star_name' into 'name'
    #         self.f_star_values[term_name] = extracted[term].to_dict()
    #
    # def _normalise_cost(self, cost, category):
    #     model_name = f'{self.config.value}_{self.charging_strategy.value}'
    #     f_star = self.f_star_values.get(category, {}).get(model_name, None)
    #
    #     if f_star in [None, 0]:  # prevent division by 0 or missing value
    #         raise ValueError(f'Missing or zero f* value for `{category}` in model {model_name}')
    #
    #     return cost / f_star
    #
    # def assemble_components(self):
    #     # Initialise assets parameters and variables
    #     self.assets['grid'] = Grid(self.model)
    #     self.assets['household'] = HouseholdLoad(self.model)
    #     self.assets['ccp'] = CommonConnectionPoint(self.model)
    #     self.assets['cp'] = ChargingPoint(self.model, self.config, self.charging_strategy)
    #     self.assets['ev'] = ElectricVehicle(self.model, self.config,
    #                                         self.charging_strategy)
    #
    #     # Initialise constraints
    #     self.assets['ccp'].initialise_constraints()
    #     self.assets['cp'].initialise_constraints()
    #     self.assets['ev'].initialise_constraints()
    #
    #     # Define objective function
    #     def obj_function(model):
    #         total_objective = 0
    #
    #         # Economic objective
    #         if self.obj_weights['economic_weight'] > 0:
    #             economic_obj = EconomicObjective(model)
    #
    #             investment_cost = (
    #                 economic_obj.investment_cost()
    #                 if self.config.value == 'config_1'
    #                 else economic_obj.investment_cost_linearised()
    #             )
    #
    #             economic_cost = (
    #                     investment_cost +
    #                     economic_obj.maintenance_cost() +
    #                     economic_obj.energy_purchase_cost()
    #             )
    #
    #             economic_cost_norm = self._normalise_cost(economic_cost, 'economic')
    #
    #             total_objective += self.obj_weights['economic_weight'] * economic_cost_norm
    #
    #         # Technical objective
    #         if self.obj_weights['technical_weight'] > 0:
    #             technical_obj = TechnicalObjective(model)
    #
    #             technical_cost = (
    #                     technical_obj.f_disc() +
    #                     technical_obj.f_peak() +
    #                     technical_obj.f_papr()
    #             )
    #
    #             technical_cost_norm = self._normalise_cost(technical_cost, 'technical')
    #
    #             total_objective += self.obj_weights['technical_weight'] * technical_cost_norm
    #
    #         # Social objective
    #         if self.obj_weights['social_weight'] > 0:
    #             social_obj = SocialObjective(model)
    #
    #             social_cost = (
    #                     social_obj.f_soc() +
    #                     social_obj.f_fair()
    #             )
    #
    #             social_cost_norm = self._normalise_cost(social_cost, 'social')
    #
    #             total_objective += self.obj_weights['social_weight'] * social_cost_norm
    #
    #         return total_objective
    #
    #     self.model.obj_function = pyo.Objective(rule=obj_function, sense=pyo.minimize)