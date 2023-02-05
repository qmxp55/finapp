import pandas as pd
import numpy as np


cortes = {
    "B": '24',
    "BO": '4',
    "CB": '16',
    "CI": '5',
    "PL": '1',
    "PO": '1',
    "E": '1',
    "DL": '1',
    "DO": '1',
}


def pago_pngi(df, cortes=cortes, month=None, year=None, get_cortes_masks=False):

    res = {i: [] for i in cortes.keys()}
    res_cortes_masks = {}

    if month is None:
        current_month = pd.to_datetime("today").strftime("%m")
    else:
        current_month = month

    if year is None:
        current_year = pd.to_datetime("today").strftime("%Y")
    else:
        current_year = year

    if month == '13':
        current_month = 1
        current_year = str(int(year) + 1)
        past_month = 12
        past_past_month = 11
        year_of_past_month = int(current_year) - 1
        year_of_past_past_month = int(current_year) - 1
    elif month == '1':
        current_month = 1
        current_year = year
        past_month = 12
        past_past_month = 11
        year_of_past_month = int(current_year) - 1
        year_of_past_past_month = int(current_year) - 1
    elif month == '2':
        current_month = 2
        current_year = year
        past_month = 1
        past_past_month = 12
        year_of_past_month = int(current_year)
        year_of_past_past_month = int(current_year) - 1
    else:
        past_month = int(current_month) - 1
        past_past_month = int(current_month) - 2
        year_of_past_month = current_year
        year_of_past_past_month = current_year
        
    first_day_current_month = pd.to_datetime(
        f"{1}/{current_month}/{current_year}", format="%d/%m/%Y"
    )
    first_day_last_month = pd.to_datetime(
        f"{1}/{past_month}/{year_of_past_month}", format="%d/%m/%Y"
    )

    for tarjeta, corte in cortes.items():
        if tarjeta in ["B", "CB"]:
            corte_min = pd.to_datetime(
                f"{corte}/{past_past_month}/{year_of_past_past_month}",
                format="%d/%m/%Y",
            )
            corte_max = pd.to_datetime(
                f"{corte}/{past_month}/{year_of_past_month}",
                format="%d/%m/%Y",
            )
        else:
            corte_min = pd.to_datetime(
                f"{corte}/{past_month}/{year_of_past_month}",
                format="%d/%m/%Y",
            )
            corte_max = pd.to_datetime(
                f"{corte}/{int(current_month)}/{current_year}",
                format="%d/%m/%Y",
            )

        keep = df["tipo de pago"] == tarjeta
        if tarjeta in ["E", "DL", "DO"]:
            keep &= df["fecha de operacion"] >= corte_min
            keep &= df["fecha de operacion"] < corte_max
        else:
            keep &= df["fecha de operacion"] > corte_min
            keep &= df["fecha de operacion"] <= corte_max

        res_cortes_masks[tarjeta] = keep
        #
        # print(tarjeta, round(df['Cargo'][keep].sum(), 2))
        res[tarjeta].append(round(df["Cargo"][keep].sum(), 2))

        keep_gf = (df["etiqueta"] == "Gasto fijo") & (keep)
        res[tarjeta].append(round(df["Cargo"][keep_gf].sum(), 2))

        keep_gnf = (df["etiqueta"] != "Gasto fijo") & (keep)
        res[tarjeta].append(round(df["Cargo"][keep_gnf].sum(), 2))

        keep = (
            (df["tipo de pago"] == tarjeta)
            & (df["fecha de operacion"] >= first_day_last_month)
            & (df["fecha de operacion"] < first_day_current_month)
        )
        res[tarjeta].append(round(df["Cargo"][keep].sum(), 2))

        keep = (
            (df["tipo de pago"] == tarjeta)
            & (df["fecha de operacion"] >= first_day_last_month)
            & (df["fecha de operacion"] < first_day_current_month)
            & (df["etiqueta"] == "Gasto fijo")
        )
        res[tarjeta].append(round(df["Cargo"][keep].sum(), 2))

        keep = (
            (df["tipo de pago"] == tarjeta)
            & (df["fecha de operacion"] >= first_day_last_month)
            & (df["fecha de operacion"] < first_day_current_month)
            & (df["etiqueta"] != "Gasto fijo")
        )
        res[tarjeta].append(round(df["Cargo"][keep].sum(), 2))

        keep_gnf_periodo = (
            (df["tipo de pago"] == tarjeta)
            & (df["fecha de operacion"] > corte_max)
            & (df["fecha de operacion"] < first_day_current_month)
            & (df["etiqueta"] != "Gasto fijo")
        )
        res[tarjeta].append(round(df["Cargo"][keep_gnf_periodo].sum(), 2))

    columns = [
        "Gastos del periodo anterior (GPA)",
        "GPA Fijos",
        "GPA No Fijos",
        "Gastos del mes anterior (GMA)",
        "GMA Fijos",
        "GMA No Fijos",
        "GMA No Fijos del periodo",
    ]
    tab = pd.DataFrame.from_dict(res, orient="index", columns=columns)
    tab.loc["Total"] = tab.sum()

    if get_cortes_masks:
        return res_cortes_masks
    else:
        return tab


def gastos_category(df, cortes=cortes, month=None, year=None):

    res = {i: [] for i in cortes.keys()}

    if month is None:
        current_month = pd.to_datetime("today").strftime("%m")
    else:
        current_month = month

    if year is None:
        current_year = pd.to_datetime("today").strftime("%Y")
    else:
        current_year = year

    if month == '13':
        current_month = 1
        current_year = str(int(year) + 1)
        past_month = 12
        past_past_month = 11
        year_of_past_month = int(current_year) - 1
        year_of_past_past_month = int(current_year) - 1
    elif month == '1':
        current_month = 1
        current_year = year
        past_month = 12
        past_past_month = 11
        year_of_past_month = int(current_year) - 1
        year_of_past_past_month = int(current_year) - 1
    elif month == '2':
        current_month = 2
        current_year = year
        past_month = 1
        past_past_month = 12
        year_of_past_month = int(current_year)
        year_of_past_past_month = int(current_year) - 1
    else:
        past_month = int(current_month) - 1
        past_past_month = int(current_month) - 2
        year_of_past_month = current_year
        year_of_past_past_month = current_year
        
    first_day_current_month = pd.to_datetime(
        f"{1}/{current_month}/{current_year}", format="%d/%m/%Y"
    )
    first_day_last_month = pd.to_datetime(
        f"{1}/{past_month}/{year_of_past_month}", format="%d/%m/%Y"
    )

    for tarjeta in res.keys():
        for etiqueta in set(df["etiqueta"]):
            keep = (
                (df["tipo de pago"] == tarjeta)
                & (df["fecha de operacion"] >= first_day_last_month)
                & (df["fecha de operacion"] < first_day_current_month)
                & (df["etiqueta"] == etiqueta)
            )
            res[tarjeta].append(round(df["Cargo"][keep].sum(), 2))

    columns = list(set(df["etiqueta"]))
    tab = pd.DataFrame.from_dict(res, orient="index", columns=columns)
    tab.loc["Total"] = tab.sum()
    tab["Total"] = tab.sum(axis=1)

    return tab


def deuda_mes(df, cortes=cortes, income=None, month=None, year=None):

    lo_que_se_debe_pagar_este_mes = {}
    tab = pago_pngi(df, cortes, month=month, year=year)
    lo_que_se_debe_pagar_este_mes["Total GPA"] = tab[
        "Gastos del periodo anterior (GPA)"
    ][["B", "BO", "CB", "CI", "PL", "PO"]].sum()
    lo_que_se_debe_pagar_este_mes["Total GMA No Fijos del periodo"] = tab[
        "GMA No Fijos del periodo"
    ][["B", "BO", "CB", "CI", "PL", "PO"]].sum()
    tab_p = pago_pngi(df, cortes, month=str(int(month) + 1), year=year)
    # tab_p = tab
    lo_que_se_debe_pagar_este_mes[
        "Total GMA Fijos del periodo en Debito/efectivo"
    ] = tab_p["GMA Fijos"][["E", "DL", "DO"]].sum()
    lo_que_se_debe_pagar_este_mes["Total necesario para este mes"] = round(
        sum(list(lo_que_se_debe_pagar_este_mes.values())), 2
    )
    lo_que_se_debe_pagar_este_mes["Disponible para este mes"] = round(
        income - lo_que_se_debe_pagar_este_mes["Total necesario para este mes"],
        2,
    )

    tab = pd.DataFrame.from_dict(
        lo_que_se_debe_pagar_este_mes, orient="index", columns=["Monto"]
    )

    return tab


def ingresos(df, month=None, year=None):

    first_day_current_month = pd.to_datetime(
        f"{1}/{month}/{year}", format="%d/%m/%Y"
    )

    if month == '2':
        last_day_current_month = pd.to_datetime(
        f"{28}/{month}/{year}", format="%d/%m/%Y"
        )
    else:
        last_day_current_month = pd.to_datetime(
        f"{30}/{month}/{year}", format="%d/%m/%Y"
        )


    total = 0
    for tarjeta in ['DL', 'DO', 'E']:

        keep = (df["fecha de operacion"] >= first_day_current_month) & (df["fecha de operacion"] <= last_day_current_month) & (df['Tarjeta'] == tarjeta)
        # print(df['Income'][keep].sum())
        total += df['Income'][keep].sum()

    return total

    # return 117000

def expenses_summary(df, month=None, year=None):

    # gasto_fijo = 0
    # msi = 0
    # gasto_no_fijo = 0

    gasto_fijo_mask = np.zeros(len(df), dtype=bool)
    msi_mask = np.zeros(len(df), dtype=bool)
    # gasto_no_fijo_mask = np.zeros(len(df), dtype=bool)

    ismsi = np.array([i == 'TRUE' for i in df['MSI']])
    is_gasto_fijo = df["etiqueta"] == "Gasto fijo"

    gastos_categoria_current = gastos_category(df=df, month=str(int(month) + 1), year=year)
    gastos_category_total = gastos_categoria_current.loc['Total', :].drop(["Total", 'Gasto fijo']).sum()

    res_cortes_masks = pago_pngi(df, cortes=cortes, month=month, year=year, get_cortes_masks=True)
    # print(df['MSI'])
    # print('is MSI?', ismsi)
    # print(np.sum(ismsi), np.sum(~ismsi))
    for tarjeta, mask in res_cortes_masks.items():
        if tarjeta in ['DL', 'DO', 'E']: 
            continue
        # gasto_fijo += df["Cargo"][mask & is_gasto_fijo & ~ismsi].sum()
        # msi += df["Cargo"][mask & is_gasto_fijo & ismsi].sum()

        gasto_fijo_mask |= (mask & is_gasto_fijo & ~ismsi)
        msi_mask |= (mask & is_gasto_fijo & ismsi)
        # print(tarjeta, '---->', round(df["Cargo"][mask & is_gasto_fijo & ~ismsi].sum(), 2), round(df["Cargo"][mask & is_gasto_fijo & ismsi].sum(), 2), round(df["Cargo"][mask & is_gasto_fijo].sum(), 2))

    res_cortes_masks = pago_pngi(df, cortes=cortes, month=str(int(month) + 1), year=year, get_cortes_masks=True)
    for tarjeta, mask in res_cortes_masks.items():
        if tarjeta not in ['DL', 'DO', 'E']: 
            continue
        # gasto_fijo += df["Cargo"][mask & is_gasto_fijo & ~ismsi].sum()
        # msi += df["Cargo"][mask & is_gasto_fijo & ismsi].sum()

        gasto_fijo_mask |= (mask & is_gasto_fijo & ~ismsi)
        msi_mask |= (mask & is_gasto_fijo & ismsi)

    # print('gasto fijo', gasto_fijo)
    # print('msi', msi)
    # print('gasto no fijo', gasto_no_fijo)

    # print('gasto fijo', df['Cargo'][gasto_fijo_mask].sum())
    # print('msi', df['Cargo'][msi_mask].sum())
    # print('gasto no fijo', gastos_category_total)

    df_sum = pd.DataFrame.from_dict({'Gastos Fijos': df['Cargo'][gasto_fijo_mask].sum(), 'MSI':df['Cargo'][msi_mask].sum(), 'Gastos No Fijos':gastos_category_total}, orient="index")
    # print(df_sum)

    return df_sum, df[gasto_fijo_mask], df[msi_mask]