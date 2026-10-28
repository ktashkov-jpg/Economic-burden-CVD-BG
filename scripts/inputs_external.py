"""External inputs retrieved from Eurostat on 27 October 2026 (API, JSON-stat)."""
# demo_r_pjanaggr3, population on 1 January 2024, NUTS3 (total; aged 65 or over)
NUTS3_POP_2024 = {
 'BG311': ('Vidin', 71773, 22431), 'BG312': ('Montana', 114526, 32269), 'BG313': ('Vratsa', 147619, 36890),
 'BG314': ('Pleven', 217881, 61512), 'BG315': ('Lovech', 112225, 31451), 'BG321': ('Veliko Tarnovo', 202232, 55467),
 'BG322': ('Gabrovo', 94862, 28716), 'BG323': ('Ruse', 187830, 50574), 'BG324': ('Razgrad', 100696, 25203),
 'BG325': ('Silistra', 94739, 26263), 'BG331': ('Varna', 434191, 93402), 'BG332': ('Dobrich', 146635, 39233),
 'BG333': ('Shumen', 149699, 37773), 'BG334': ('Targovishte', 95609, 24324), 'BG341': ('Burgas', 384446, 86611),
 'BG342': ('Sliven', 170051, 38019), 'BG343': ('Yambol', 106320, 28483), 'BG344': ('Stara Zagora', 290350, 71343),
 'BG411': ('Sofia (capital)', 1286965, 247474), 'BG412': ('Sofia (province)', 226420, 54413), 'BG413': ('Blagoevgrad', 287077, 63609),
 'BG414': ('Pernik', 111032, 29026), 'BG415': ('Kyustendil', 107673, 30649), 'BG421': ('Plovdiv', 633586, 142393),
 'BG422': ('Haskovo', 207114, 53381), 'BG423': ('Pazardzhik', 225261, 54652), 'BG424': ('Smolyan', 92107, 26616),
 'BG425': ('Kardzhali', 146562, 38732)}
# NHIF regional health insurance fund (RZOK) number -> NUTS3
RZOK_NUTS3 = {1:'BG413',2:'BG341',3:'BG331',4:'BG321',5:'BG311',6:'BG313',7:'BG322',8:'BG332',9:'BG425',10:'BG415',
 11:'BG315',12:'BG312',13:'BG423',14:'BG414',15:'BG314',16:'BG421',17:'BG324',18:'BG323',19:'BG325',20:'BG342',
 21:'BG424',22:'BG411',23:'BG412',24:'BG344',25:'BG334',26:'BG422',27:'BG333',28:'BG343'}
# prc_hicp_aind, Bulgaria, all-items HICP, annual average index (2015 = 100)
HICP = {2021: 109.30, 2022: 123.52, 2023: 134.15, 2024: 137.63, 2025: 142.50}
EUR = 1.95583  # fixed BGN per EUR
