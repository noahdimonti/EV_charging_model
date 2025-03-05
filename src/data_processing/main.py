import vista_data_cleaning as vdc
import generate_ev_dep_arr_data as gda
import generate_synthetic_ev_data as gse
from src.config import params
from pprint import pprint


def main():
    return gse.main(params.num_of_evs, f'EV_instances_{params.num_of_evs}')


if __name__ == '__main__':
    main()

# weekday, weekend_list = vdc.main()
#
# # for i in range(2):
# #     test = gev.create_multiple_weeks_dep_arr_time(2, weekday, weekend_list, i, i)
# #     pprint(test)
#
#
# evlst = gens.main(3)
# pprint(evlst[0].__dict__)
# pprint(evlst[1].__dict__)
#
# # test = gens.generate_ev_attributes(2, 14, weekday, weekend_list)
# # test = gens.generate_travel_energy_consumption(20, 1, 5)