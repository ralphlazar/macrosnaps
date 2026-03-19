#!/usr/bin/env python3
"""
add_russia.py — Injects Russia (RUS) into macrosnaps-globe.html

Adds:
  1. RUS country object into <script id="countries-data"> JSON
  2. 4 glossary terms (CBR, MOEX, ruble, key rate) into <script id="glossary-data"> JSON

Usage:
    python3 add_russia.py macrosnaps-globe.html
"""

import json
import sys
import re

# ───────────────────────────────────────────────────────────────
# RUS country data
# ───────────────────────────────────────────────────────────────

RUS_COUNTRY = {
    "code": "RUS",
    "name": "Russia",
    "flag": "🇷🇺",
    "lat": 55.75,
    "lon": 37.62,
    "weather": "⛈️",
    "metrics": {
        "macro": {
            "GDP Growth": "+1.0%",
            "Inflation (CPI)": "4.7%",
            "Unemployment": "2.2%",
            "Budget Deficit": "-2.5% GDP",
            "Current Account": "+2.0% GDP",
            "Policy Rate": "21.00%"
        },
        "market": {
            "Stock Market YTD": "+12.0%",
            "Equity Vol": "~28",
            "10Y Bond Yield": "14.60%",
            "Yield Curve": "-140bps",
            "Corp Spread": "350bps",
            "Sov CDS": "300bps",
            "USD/RUB": "97.2",
            "FX Vol": "18.0%"
        }
    },
    "stories": {
        "beginner": [
            "Russia's economy has shifted to a war footing — military spending now absorbs over 7% of GDP, the highest since the Soviet era. This has driven record-low unemployment (2.2%) but created severe labor shortages in civilian industries",
            "The Central Bank of Russia (CBR) has raised its key rate to 21% — one of the highest in the world — to combat inflation fueled by massive government spending and worker shortages. Prices for everyday goods remain under pressure",
            "Western sanctions have reshaped Russia's trade: China and India now buy most of its oil, the ruble is propped up by capital controls, and the Moscow Exchange no longer trades dollars or euros directly"
        ],
        "moderate": [
            "GDP growth collapsed from 4.3% (2024) to ~1.0% (2026F) as the wartime stimulus fades and capacity constraints bite. Defense spending at 7.3% of GDP — crowding out civilian investment. Labor market at 2.2% unemployment masks acute shortages: manufacturing and construction vacancies at record highs, wage growth ~15% YoY in affected sectors, feeding services inflation",
            "CBR holding key rate at 21% — the most restrictive stance since 2003. Real rates ~16% but transmission is impaired: ~30% of new corporate lending is government-directed or subsidized (defense contracts, import substitution programs), effectively bypassing the rate channel. Inflation at ~4.7% but core measures remain elevated; CBR flagging persistent demand-side pressures",
            "Fiscal position deteriorating: budget deficit widened to ~2.5% of GDP as energy revenues decline (oil price cap + lower volumes) while military spending is structurally higher. National Wealth Fund (NWF) drawdown accelerating — liquid assets fell from ~$120bn (2022) to ~$55bn. VAT hiked from 20% to 22% in January 2025 to partly offset the gap"
        ],
        "expert": [
            "Wartime macro regime: fiscal multiplier from defense spending (~7.3% GDP, up from 3.5% pre-war) generated 2023-24 overheating but is now encountering hard supply constraints. Potential output permanently impaired by: emigration (~700k skilled workers since 2022), redirected R&D toward military applications, and capital stock deterioration in sanctions-restricted sectors. GDP ~1.0% masks composition — military-adjacent sectors growing 15-20% while civilian manufacturing contracts",
            "CBR operating in a structurally impaired transmission environment: key rate at 21% (ex-ante real rate ~16%) but effective economy-wide rate substantially lower due to directed lending (~30% of new credit bypasses rate channel via subsidized defense/import-substitution programs). Corporate bond market dislocated — OFZ (government bond) curve deeply inverted (-140bp 10Y-key rate), reflecting both expectations of eventual easing and limited foreign participation. Inflation targeting framework functionally constrained by fiscal dominance",
            "External sector paradox: current account surplus (~2% GDP) masks structural vulnerability. Export revenues increasingly concentrated in energy-to-China/India corridor (~65% of oil exports) at sanctioned discounts (~$15-20/bbl below Brent). Capital controls (mandatory FX revenue repatriation, limits on offshore transfers) sustain ruble stability but create a dual exchange rate reality — CBR official rate (~97 RUB/USD based on OTC interbank data since MOEX halted USD/EUR trading Jun 2024) diverges from offshore NDF pricing. NWF liquid assets at ~$55bn (was ~$120bn) providing diminishing fiscal buffer. Yuan now primary hard-currency pair on MOEX (~40% of FX turnover)"
        ]
    },
    "fxRegime": {
        "label": "Managed Float (Capital Controls)",
        "beginner": "Russia's ruble is officially a floating currency, but it's tightly managed through capital controls. After sanctions hit in 2022, the government required exporters to convert their foreign currency earnings into rubles, which helped stabilize the exchange rate. The Moscow Exchange stopped trading dollars and euros in June 2024, so the official rate is now set by the central bank using data from banks trading among themselves. USD/RUB tells you how many rubles one US dollar costs.",
        "moderate": "Managed float with extensive capital controls imposed since Feb 2022 and progressively tightened. The CBR sets the official USD/RUB rate using OTC interbank transaction data after MOEX halted USD and EUR trading (June 2024, following US sanctions on the exchange itself). Mandatory FX revenue repatriation requirements for exporters (~80% initially, now ~50%) support the rate. ~60% of Russian exports are now invoiced in rubles (up from 14% in 2021). The Chinese yuan is the primary hard-currency trading pair on MOEX, accounting for ~40% of FX turnover.",
        "expert": "De facto managed float with capital controls creating a dual exchange rate regime. CBR computes the official USD/RUB fix from OTC interbank data (methodology shift post-June 2024 MOEX USD/EUR trading halt after OFAC sanctioned NCC/NSD clearing infrastructure). Onshore rate (~97) diverges from offshore NDF pricing by 3-8% depending on sanctions enforcement intensity. Key FX management tools: (1) mandatory export revenue repatriation (50% threshold, periodically adjusted); (2) informal capital outflow restrictions; (3) CBR FX interventions via fiscal rule mechanism (suspended 2022-23, partially resumed). Reserve position ~$300bn gross but ~$200bn frozen (EU/G7 jurisdictions). Yuan-ruble pair dominates MOEX FX turnover (~40%), creating indirect CNY peg characteristics. Ruble dynamics now primarily driven by oil revenue volume (not price — discounts are structural), fiscal deficit financing needs, and capital control enforcement rather than traditional EM FX factors."
    },
    "historical": {
        "GDP Growth": {
            "v": [-2.7, 5.9, -1.2, 3.6, 4.3, 1.8, 1.0],
            "annual": True,
            "type": "bar"
        },
        "Inflation (CPI)": {
            "v": [3.4, 6.7, 11.9, 7.4, 7.4, 5.8, 4.7],
            "annual": True,
            "type": "line"
        },
        "Unemployment": {
            "v": [5.8, 4.8, 3.9, 3.2, 2.4, 2.3, 2.5],
            "annual": True,
            "type": "line"
        },
        "Policy Rate": {
            "v": [4.25, 8.5, 7.5, 16.0, 21.0, 21.0, 16.0],
            "annual": True,
            "type": "line"
        },
        "10Y Bond Yield": {
            "v": [5.9, 8.4, 10.5, 12.2, 14.8, 14.6, 13.5],
            "annual": True,
            "type": "line"
        },
        "Stock Market YTD": {
            "v": [8.0, 15.1, -43.1, 43.9, -7.0, 6.0, 12.0],
            "annual": True,
            "type": "bar"
        }
    },
    "weatherGrid": {
        "gdp": {
            "flag": "🇷🇺",
            "values": [-2.7, 5.9, -1.2, 3.6, 4.3, 1.8, 1.0]
        },
        "cpi": {
            "flag": "🇷🇺",
            "values": [3.4, 6.7, 11.9, 7.4, 7.4, 5.8, 4.7]
        },
        "unemp": {
            "flag": "🇷🇺",
            "values": [5.8, 4.8, 3.9, 3.2, 2.4, 2.3, 2.5]
        },
        "budget": {
            "flag": "🇷🇺",
            "values": [-3.8, -0.4, -1.4, -1.9, -1.7, -2.2, -2.5]
        },
        "ca": {
            "flag": "🇷🇺",
            "values": [2.4, 6.6, 10.5, 3.3, 2.9, 2.3, 2.0]
        }
    }
}

# ───────────────────────────────────────────────────────────────
# Glossary terms to add
# ───────────────────────────────────────────────────────────────

RUS_GLOSSARY = {
    "CBR": {
        "complexity": 2,
        "category": "institutions",
        "levels": {
            "beginner": {
                "bluf": "The Central Bank of Russia (CBR) — Russia's central bank that sets the key interest rate and manages monetary policy. It also sets the official ruble exchange rate.",
                "full": None
            },
            "moderate": {
                "bluf": "Bank of Russia (CBR) — responsible for price stability (4% inflation target) and financial system oversight. Sets the key rate via Board of Directors meetings (8 per year). Since June 2024, also computes the official USD/RUB rate from OTC interbank data after MOEX halted dollar trading.",
                "full": None
            },
            "expert": {
                "bluf": "CBR operates under a formal inflation targeting regime (4% target, adopted 2015) with the key rate as primary instrument. Transmission severely impaired post-2022: ~30% of new corporate credit is government-directed (defense, import substitution) at subsidized rates, bypassing the rate channel. FX policy shifted from free float to managed regime with capital controls post-sanctions. Official rate computation methodology changed June 2024 from MOEX fixing to OTC interbank data. Gross reserves ~$300bn but ~$200bn frozen in EU/G7 jurisdictions.",
                "full": None
            }
        }
    },
    "MOEX": {
        "complexity": 2,
        "category": "equity",
        "levels": {
            "beginner": {
                "bluf": "The Moscow Exchange (MOEX) is Russia's main stock and currency exchange. The MOEX Russia Index tracks the largest Russian companies. Since 2024, it no longer trades US dollars or euros.",
                "full": None
            },
            "moderate": {
                "bluf": "Moscow Exchange (MOEX) — Russia's primary securities and derivatives exchange. The MOEX Russia Index (IMOEX) is the ruble-denominated benchmark, heavily weighted toward energy (Gazprom, Rosneft, Lukoil ~40%), financials (Sberbank ~15%), and metals. Foreign investor access restricted since 2022 — non-resident shares frozen, decoupling the index from global EM flows.",
                "full": None
            },
            "expert": {
                "bluf": "MOEX: Russia's vertically integrated exchange (equities, bonds, FX, derivatives, money market). IMOEX composition: energy ~40%, financials ~15%, metals/mining ~12%. Post-sanctions regime: non-resident holdings frozen (~$40bn), FX segment restructured (USD/EUR pairs halted June 2024 after OFAC sanctioned NCC clearing infrastructure). Yuan-ruble pair now dominates FX turnover (~40%). Equity valuations compressed (P/E ~4-5x) reflecting trapped capital, sanctions discount, and limited exit routes for foreign holders.",
                "full": None
            }
        }
    },
    "ruble": {
        "complexity": 1,
        "category": "fx",
        "levels": {
            "beginner": {
                "bluf": "The ruble (₽, RUB) is Russia's currency. USD/RUB tells you how many rubles one US dollar can buy. The rate is now set by the central bank rather than free market trading.",
                "full": None
            },
            "moderate": {
                "bluf": "The Russian ruble (RUB) — a managed currency under capital controls since 2022. The CBR sets the official rate from OTC interbank data after MOEX halted dollar trading (June 2024). Export revenue repatriation requirements and restricted capital outflows support the rate artificially. The onshore rate diverges from offshore NDF pricing.",
                "full": None
            },
            "expert": {
                "bluf": "RUB: de facto managed currency with capital controls creating onshore/offshore rate divergence (3-8% spread). CBR official rate (~97/USD) derived from OTC interbank data post-MOEX USD halt. Key dynamics: (1) export repatriation requirements (50% threshold) anchor supply; (2) capital outflow restrictions limit demand; (3) yuan has replaced USD as primary hard-currency pair on MOEX (~40% FX turnover). Gross reserves ~$300bn but ~$200bn frozen. Rate sensitivity now more to oil export volumes than prices (structural discounts to Brent of $15-20/bbl).",
                "full": None
            }
        }
    },
    "key rate": {
        "complexity": 2,
        "category": "macro",
        "levels": {
            "beginner": {
                "bluf": "Russia's key rate is the main interest rate set by the Central Bank of Russia (CBR) — similar to the Fed funds rate in the US. At 21%, it's one of the highest in the world.",
                "full": None
            },
            "moderate": {
                "bluf": "The CBR key rate is the minimum interest rate for one-week repo and deposit operations with the central bank. At 21%, it represents an ex-ante real rate of ~16% — extremely restrictive, aimed at cooling wartime inflation driven by fiscal expansion and labor shortages.",
                "full": None
            },
            "expert": {
                "bluf": "CBR key rate: minimum auction rate for 1-week repo and maximum rate for 1-week deposit operations, forming the center of the interest rate corridor (±1pp). Currently 21% — highest since 2003. Ex-ante real rate ~16%, but effective economy-wide restrictiveness lower due to ~30% directed/subsidized credit share bypassing transmission. Rate held at 21% since Oct 2024 despite inflation moderating to ~4.7%, reflecting CBR concern over persistent core pressures and fiscal-driven demand.",
                "full": None
            }
        }
    }
}


# ───────────────────────────────────────────────────────────────
# Main injection logic
# ───────────────────────────────────────────────────────────────

def extract_json_block(html, script_id):
    """Extract JSON content between <script id="..."> and </script>."""
    pattern = f'<script type="application/json" id="{script_id}">'
    start = html.index(pattern) + len(pattern)
    end = html.index('</script>', start)
    return start, end, html[start:end]


def inject(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # ── 1. Inject RUS into countries-data ──
    c_start, c_end, c_json = extract_json_block(html, "countries-data")
    countries = json.loads(c_json)

    if "RUS" in countries:
        print("⚠️  RUS already exists in countries-data — overwriting")
    countries["RUS"] = RUS_COUNTRY
    new_c_json = json.dumps(countries, indent=2, ensure_ascii=False)
    html = html[:c_start] + "\n" + new_c_json + "\n" + html[c_end:]

    # ── 2. Inject glossary terms into glossary-data ──
    g_start, g_end, g_json = extract_json_block(html, "glossary-data")
    glossary = json.loads(g_json)

    added = []
    for term, data in RUS_GLOSSARY.items():
        if term in glossary:
            print(f"⚠️  Glossary term '{term}' already exists — overwriting")
        glossary[term] = data
        added.append(term)
    new_g_json = json.dumps(glossary, indent=2, ensure_ascii=False)
    html = html[:g_start] + "\n" + new_g_json + "\n" + html[g_end:]

    # ── 3. Write back ──
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    country_count = len(countries)
    glossary_count = len(glossary)
    print(f"✅ Injected RUS into countries-data ({country_count} countries total)")
    print(f"✅ Added glossary terms: {', '.join(added)} ({glossary_count} terms total)")
    print(f"✅ File written: {html_path}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "macrosnaps-globe.html"
    inject(path)
