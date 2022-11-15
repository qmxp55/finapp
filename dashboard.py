import pandas as pd


cortes = {
    "B": 24,
    "BO": 4,
    "CB": 16,
    "CI": 5,
    "PL": 1,
    "PO": 1,
    "E": 1,
    "DL": 1,
    "DO": 1,
}


def pago_pngi(df, cortes, month=None, year=None):

    res = {i: [] for i in cortes.keys()}

    if month is None:
        current_month = pd.to_datetime("today").strftime("%m")
    else:
        current_month = month

    if year is None:
        current_year = pd.to_datetime("today").strftime("%y")
    else:
        current_year = year

    first_day_current_month = pd.to_datetime(
        f"{1}/{int(current_month)}/{current_year}", format="%d/%m/%y"
    )
    first_day_last_month = pd.to_datetime(
        f"{1}/{int(current_month) - 1}/{current_year}", format="%d/%m/%y"
    )

    for tarjeta, corte in cortes.items():
        if tarjeta in ["B", "CB"]:
            corte_min = pd.to_datetime(
                f"{corte}/{int(current_month) - 2}/{current_year}",
                format="%d/%m/%y",
            )
            corte_max = pd.to_datetime(
                f"{corte}/{int(current_month) - 1}/{current_year}",
                format="%d/%m/%y",
            )
        else:
            corte_min = pd.to_datetime(
                f"{corte}/{int(current_month) - 1}/{current_year}",
                format="%d/%m/%y",
            )
            corte_max = pd.to_datetime(
                f"{corte}/{int(current_month)}/{current_year}",
                format="%d/%m/%y",
            )

        keep = df["tipo de pago"] == tarjeta
        if tarjeta in ["E", "DL", "DO"]:
            keep &= df["fecha de operacion"] >= corte_min
            keep &= df["fecha de operacion"] < corte_max
        else:
            keep &= df["fecha de operacion"] > corte_min
            keep &= df["fecha de operacion"] <= corte_max
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

    return tab


def gastos_category(df, cortes, month=None, year=None):

    res = {i: [] for i in cortes.keys()}

    if month is None:
        current_month = pd.to_datetime("today").strftime("%m")
    else:
        current_month = month

    if year is None:
        current_year = pd.to_datetime("today").strftime("%y")
    else:
        current_year = year

    first_day_current_month = pd.to_datetime(
        f"{1}/{int(current_month)}/{current_year}", format="%d/%m/%y"
    )
    first_day_last_month = pd.to_datetime(
        f"{1}/{int(current_month) - 1}/{current_year}", format="%d/%m/%y"
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


def deuda_mes(df, income=None):

    lo_que_se_debe_pagar_este_mes = {}
    tab = pago_pngi(df, cortes)
    lo_que_se_debe_pagar_este_mes["Total GPA"] = tab[
        "Gastos del periodo anterior (GPA)"
    ][["B", "BO", "CB", "CI", "PL", "PO"]].sum()
    lo_que_se_debe_pagar_este_mes["Total GMA No Fijos del periodo"] = tab[
        "GMA No Fijos del periodo"
    ][["B", "BO", "CB", "CI", "PL", "PO"]].sum()
    tab_p = pago_pngi(df, cortes, month="12", year="22")
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


def ingresos():

    return 117000
