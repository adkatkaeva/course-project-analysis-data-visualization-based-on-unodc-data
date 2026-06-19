# course-project-analysis-data-visualization-based-on-unodc-data
Репозиторий курсового проекта "Анализ и визуализация данных с использованием Yandex Datalens, на примере данных UNODC". 

**Структура репозитория**
```
.
├── README.md
├── preprocessed_data/             # Предобработанные данные
│   ├── wpp/                       
│   │   ├── wpp.xlsx               # Данные по общему населению
│   │   ├── wpp_male.xlsx          # Данные по населению мужчин
│   │   └── wpp_female.xlsx        # Данные по населению женщин
│   └── unodc/
│       └── unodc.xlsx             # Данные по умышленным убийствам
├── raw_data/
│   ├── wpp_raw/                   # Исходные данные датасета World Population Prospects
│   │   ├── wpp.xlsx               
│   │   ├── wpp_male.xlsx         
│   │   └── wpp_female.xlsx     
│   └── unodc_raw/                 # Исходные данные датасета UNODC
│   │   └── unodc.xlsx
│   └── geo_raw/                   # Исходные данные датасета от компании Геоинтеллект
│       └── geo.xlsx
├── data_processing/               # Обработка данных
│   ├── data_processing.py         # Цельный код
│   └── data_processing.pynb       # Python-ноутбук
└── prepared_data/                 # Уже подготовленные данные
    ├── unodc_main.csv
    ├── wpp_population.csv
    └── geo_borders.csv
```
