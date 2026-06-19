import pandas as pd
import numpy as np

# Имена выходных файлов
OUT_UNODC = "unodc_main.csv"
OUT_WPP = "wpp_population.csv"
OUT_BORDERS = "geo_borders.csv"

# Словарь соответствий названий стран между UNODC и WPP
UNODC_TO_WPP = {
    "China, Hong Kong Special Administrative Region": "China, Hong Kong SAR",
    "China, Macao Special Administrative Region": "China, Macao SAR",
    "Iraq (Central Iraq)": "Iraq",
    "Kosovo under UNSCR 12414": "Kosovo (under UNSC res. 1244)",
    "Micronesia (Federated States of)": "Micronesia (Fed. States of)",
    "Netherlands (Kingdom of the)": "Netherlands",
}

# Обратное отображение: из названий WPP в названия UNODC
WPP_TO_UNODC = {v: k for k, v in UNODC_TO_WPP.items()}


def process_wpp_file(filepath, sex_label):
    """
    Читает файл WPP, отбирает страны и годы 2019–2023,
    рассчитывает нужные возрастные группы и возвращает таблицу
    в длинном формате: страна, год, пол, возрастная группа, население.
    """
    # Файл может быть CSV или Excel; заголовок может быть на первой или второй строке
    if filepath.endswith(".csv"):
        df_raw = pd.read_csv(filepath, header=1)
        if "Type" not in df_raw.columns:
            df_raw = pd.read_csv(filepath, header=0)
    else:
        df_raw = pd.read_excel(filepath, sheet_name=0, header=1)
        if "Type" not in df_raw.columns:
            df_raw = pd.read_excel(filepath, sheet_name=0, header=0)

    # Оставляем только записи по странам и по нужным годам
    df = df_raw[
        (df_raw["Type"] == "Country/Area") &
        (df_raw["Year"].between(2019, 2023))
    ].copy()

    # Переименовываем основные столбцы
    df.rename(
        columns={
            "Region, subregion, country or area *": "country_wpp",
            "Year": "year"
        },
        inplace=True
    )

    # Формируем возрастные группы, согласованные с UNODC
    df["pop_Все"] = df["Total"]
    df["pop_0-9"] = df["0-4"] + df["5-14"] / 2
    df["pop_10-14"] = df["5-14"] / 2
    df["pop_15-17"] = df["15-17"]
    df["pop_18-19"] = df["0-19"] - df["0-17"]
    df["pop_20-24"] = df["0-24"] - df["0-19"]
    df["pop_25-29"] = df["25-49"] / 5
    df["pop_30-44"] = df["25-49"] * 3 / 5
    df["pop_45-59"] = df["25-49"] / 5 + (df["50+"] - df["60+"])
    df["pop_60 и старше"] = df["60+"]

    # Приводим названия стран к формату UNODC
    df["country_en"] = df["country_wpp"].map(WPP_TO_UNODC).fillna(df["country_wpp"])

    # Список итоговых возрастных групп и соответствующих столбцов
    pop_cols = {
        "Все": "pop_Все",
        "0-9": "pop_0-9",
        "10-14": "pop_10-14",
        "15-17": "pop_15-17",
        "18-19": "pop_18-19",
        "20-24": "pop_20-24",
        "25-29": "pop_25-29",
        "30-44": "pop_30-44",
        "45-59": "pop_45-59",
        "60 и старше": "pop_60 и старше"
    }

    # Переводим в длинный формат
    parts = []
    for age_group, col in pop_cols.items():
        if col in df.columns:
            tmp = df[["country_en", "year", col]].copy()
            tmp.columns = ["country_en", "year", "pop_thousands"]
            tmp["age_group"] = age_group
            tmp["sex"] = sex_label
            parts.append(tmp)

    return pd.concat(parts, ignore_index=True).dropna(subset=["pop_thousands"])


# Обрабатываем данные WPP для общего населения, мужчин и женщин
wpp_total = process_wpp_file("wpp.xlsx", "Все")
wpp_male = process_wpp_file("wpp_male.xlsx", "Мужчины")
wpp_female = process_wpp_file("wpp_female.xlsx", "Женщины")

# Объединяем все WPP-данные в одну таблицу
df_wpp_long = pd.concat([wpp_total, wpp_male, wpp_female], ignore_index=True)
df_wpp_long["pop_thousands"] = df_wpp_long["pop_thousands"].round(3)

# Подготавливаем словарь населения United Kingdom для последующей агрегации частей страны
uk_pop_lookup = (
    df_wpp_long[df_wpp_long["country_en"] == "United Kingdom"]
    .set_index(["year", "sex", "age_group"])["pop_thousands"]
    .to_dict()
)

# Загружаем исходный файл UNODC
df_raw = pd.read_excel(
    "data_cts_intentional_homicide.xlsx",
    sheet_name="умышленные_убийства_данные"
)

# Переименовываем столбцы в короткие и понятные рабочие имена
col_rename = {}
for col in df_raw.columns:
    if "Код ISO-3" in str(col):
        col_rename[col] = "iso3"
    elif "Страна" in str(col) or "Название страны" in str(col):
        col_rename[col] = "country_ru"
    elif "Country" in str(col):
        col_rename[col] = "Country"
    elif "Регион" in str(col):
        col_rename[col] = "region_ru"
    elif "Region" in str(col):
        col_rename[col] = "Region"
    elif "Субрегион" in str(col):
        col_rename[col] = "subregion_ru"
    elif "Subregion" in str(col):
        col_rename[col] = "Subregion"
    elif "Год" in str(col):
        col_rename[col] = "year"
    elif "Пол" in str(col):
        col_rename[col] = "sex"
    elif "Возраст" in str(col):
        col_rename[col] = "age_raw"
    elif "Показатель" in str(col):
        col_rename[col] = "indicator"
    elif "Характер" in str(col):
        col_rename[col] = "nature"
    elif "Единица измерения" in str(col):
        col_rename[col] = "unit"
    elif "Категория" in str(col):
        col_rename[col] = "category"
    elif "Значение" in str(col):
        col_rename[col] = "value"

df_raw.rename(columns=col_rename, inplace=True)

# Оставляем только нужные записи:
# жертвы умышленного убийства, характер = "Все", категория = "Все", годы 2019–2023
df = df_raw[
    (df_raw["indicator"] == "Жертвы умышленного убийства") &
    (df_raw["nature"] == "Все") &
    (df_raw["category"] == "Все") &
    (df_raw["year"].between(2019, 2023))
].copy()

# Нормализуем возрастные группы
df["age_group"] = (
    df["age_raw"]
    .astype(str)
    .str.strip()
    .str.replace("10 -14", "10-14")
    .str.replace("15 -17", "15-17")
)

# Исключаем строки с неизвестным возрастом
df = df[df["age_group"] != "Неизвестно"].copy()

# Переводим названия регионов на английский
region_mapping = {
    "Азия": "Asia",
    "Америка": "Americas",
    "Африка": "Africa",
    "Европа": "Europe",
    "Океания": "Oceania"
}

df["Region"] = df["region_ru"].map(region_mapping).fillna(df["region_ru"])
df["Subregion"] = df["subregion_ru"]

# Отдельно берем абсолютные значения
df_count = df[df["unit"] == "Количество"][
    [
        "iso3", "country_ru", "Country", "region_ru", "Region",
        "subregion_ru", "Subregion", "year", "sex", "age_group", "value"
    ]
].rename(columns={"value": "count"})

# Отдельно берем показатели на 100 000 населения
df_rate = df[df["unit"] == "На 100,000 населения"][
    ["year", "sex", "age_group", "Country", "value"]
].rename(columns={"value": "rate_per_100k"})

# Объединяем count и rate в одну таблицу
df_wide = df_count.merge(
    df_rate,
    on=["year", "sex", "age_group", "Country"],
    how="outer"
)

# Переводим числовые поля к numeric
df_wide["count"] = pd.to_numeric(df_wide["count"], errors="coerce")
df_wide["rate_per_100k"] = pd.to_numeric(df_wide["rate_per_100k"], errors="coerce")

# Приводим обозначения пола к единому виду
df_wide["sex"] = df_wide["sex"].replace({
    "Мужчина": "Мужчины",
    "Женщина": "Женщины"
})

# В UNODC части UK могут идти отдельно, поэтому сначала отделяем их
UK_PARTS = [
    "United Kingdom (England and Wales)",
    "United Kingdom (Northern Ireland)",
    "United Kingdom (Scotland)"
]

df_uk = df_wide[df_wide["Country"].isin(UK_PARTS)].copy()
df_non_uk = df_wide[~df_wide["Country"].isin(UK_PARTS)].copy()


def merge_uk(df_uk, uk_pop_lookup):
    """
    Объединяет части Великобритании в одну страну.
    Суммирует абсолютное количество и пересчитывает значение через население WPP.
    """
    groups = df_uk.groupby(["year", "sex", "age_group"])
    rows = []

    for (year, sex, age), grp in groups:
        total_count = grp["count"].sum(skipna=True)
        pop_thousands = uk_pop_lookup.get((year, sex, age), np.nan)

        # Если есть население, считаем значение заново
        # Иначе используем среднее из доступных rate как резервный вариант
        if pd.notna(pop_thousands) and pop_thousands > 0:
            rate_uk = (total_count / (pop_thousands * 1000)) * 100_000
        else:
            rate_uk = grp["rate_per_100k"].mean(skipna=True)

        rows.append({
            "iso3": "GBR",
            "country_ru": "Великобритания",
            "Country": "United Kingdom",
            "region_ru": "Европа",
            "Region": "Europe",
            "subregion_ru": "Северная Европа",
            "Subregion": "Northern Europe",
            "year": year,
            "sex": sex,
            "age_group": age,
            "count": total_count,
            "rate_per_100k": round(rate_uk, 6) if pd.notna(rate_uk) else np.nan,
            "uk_partial": (age != "Все")
        })

    return pd.DataFrame(rows)


# Объединяем части UK и собираем итоговую таблицу UNODC
df_uk_merged = merge_uk(df_uk, uk_pop_lookup)
df_result = pd.concat([df_non_uk, df_uk_merged], ignore_index=True)

# Удаляем технический столбец, если он появился
if "uk_partial" in df_result.columns:
    df_result.drop(columns=["uk_partial"], inplace=True)

# В таблице WPP приводим название столбца страны к общему имени
df_wpp_long.rename(columns={"country_en": "Country"}, inplace=True)

# Загружаем данные по границам стран
df_borders = pd.read_csv("all_country_borders.csv", sep=";")

# Оставляем только полигоны границ стран
df_borders = df_borders[
    df_borders["coords_type"] == "all_country_borders_poly"
].copy()

# Приводим названия стран из геоданных к формату UNODC
BORDERS_TO_UNODC = {
    "The Bahamas": "Bahamas",
    "Bolivia": "Bolivia (Plurinational State of)",
    "Cape Verde": "Cabo Verde",
    "Iraq": "Iraq (Central Iraq)",
    "Kosovo": "Kosovo under UNSCR 1244",
    "Federated States of Micronesia": "Micronesia (Federated States of)",
    "Netherlands": "Netherlands (Kingdom of the)",
    "South Korea": "Republic of Korea",
    "Moldova": "Republic of Moldova",
    "Russia": "Russian Federation",
    "Turkey": "Türkiye",
    "Tanzania": "United Republic of Tanzania",
    "United States": "United States of America",
    "Venezuela": "Venezuela (Bolivarian Republic of)",
    "Brunei": "Brunei Darussalam",
    "Congo-Brazzaville": "Congo",
    "East Timor": "Timor-Leste",
    "Iran": "Iran (Islamic Republic of)",
    "Laos": "Lao People's Democratic Republic",
    "North Korea": "Dem. People's Republic of Korea",
    "Syria": "Syrian Arab Republic",
    "São Tomé and Príncipe": "Sao Tome and Principe",
    "The Gambia": "Gambia",
    "Vietnam": "Viet Nam",
    "Vatican City": "Holy See",
}

df_borders["Country"] = df_borders["name_en"].replace(BORDERS_TO_UNODC)

# Оставляем только нужные столбцы для финального файла
df_borders_out = df_borders[["Country", "coords_type", "coords"]].copy()

# Сохраняем три итоговые таблицы
df_result.to_csv(OUT_UNODC, index=False, encoding="utf-8-sig")
df_wpp_long.to_csv(OUT_WPP, index=False, encoding="utf-8-sig")
df_borders_out.to_csv(OUT_BORDERS, index=False, encoding="utf-8-sig")

# Если нужны проверки несовпадений стран между наборами данных,
# можно сохранить их в переменные без вывода на экран
unodc_countries = set(df_result["Country"].dropna().unique())
wpp_countries = set(df_wpp_long["Country"].dropna().unique())
geo_countries = set(df_borders_out["Country"].dropna().unique())

unodc_not_in_wpp = sorted(unodc_countries - wpp_countries)
wpp_not_in_unodc = sorted(wpp_countries - unodc_countries)
unodc_not_in_geo = sorted(unodc_countries - geo_countries)
geo_not_in_unodc = sorted(geo_countries - unodc_countries)

unodc_age_groups = sorted(df["age_group"].unique())
wpp_age_groups = sorted(df_wpp_long["age_group"].unique())