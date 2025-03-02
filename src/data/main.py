import vista_data_cleaning as vdc
import generate_ev_availability_data as gev
import generate_synthetic_ev_data as gens
from pprint import pprint

weekday, weekend_list = vdc.main()



# test = gev.main(0, 0)
# test2 = gev.main(1, 1)

for i in range(2):
    test = gev.main(i, i)
    print(f'test: {i}')
    pprint(test[40:70])

