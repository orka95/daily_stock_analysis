# -*- coding: utf-8 -*-
"""
===================================
台股代碼工具
===================================

提供：
1. 台股代碼辨識（4~5 位數字）
2. 台股代碼轉換為 Yahoo Finance 格式（XXXX.TW / XXXX.TWO）

台灣股市說明：
- 上市（TWSE）：主要為 4 位數字，Yahoo Finance 後綴 .TW
- 上櫃（TPEx）：主要為 4~5 位數字，Yahoo Finance 後綴 .TWO
- ETF：通常為 6 位（如 0050、00878），仍使用 .TW / .TWO

注意：4 位純數字可能與 A 股 ETF 混淆，
透過 is_tw_stock_code() 明確指定台股前綴 "TW" 來區分。
"""

import re

# 上市股票代碼前綴 -> .TW
# 上櫃股票代碼前綴 -> .TWO
# 本模組採用「TW」前綴方式，由使用者明確標記台股
# 例如：TW2330、TW00878

# 台股代碼正則（帶 TW 前綴）
_TW_STOCK_PATTERN = re.compile(r'^TW(\d{4,6})([A-Z]?)$', re.IGNORECASE)

# 已知上市（.TW）代碼前綴特徵（數字範圍）
# 若無法判斷，預設為 .TW（上市）
# 使用者可在代碼後加 'O' 標記為上櫃：TW6488O -> 6488.TWO
_TPEx_SUFFIX = 'O'  # 使用者加 O 後綴表示上櫃

# 常見台灣大型 ETF，直接列表（上市 .TW）
TW_ETF_CODES = {
    '0050', '0051', '0052', '0053', '0054', '0055', '0056',
    '00878', '00713', '00757', '00720B', '006208',
}


def is_tw_stock_code(code: str) -> bool:
    """
    判斷是否為台股代碼（需有 TW 前綴）。

    接受格式：
    - 'TW2330'   -> 台積電（上市）
    - 'TW6488O'  -> 上櫃股票（O 後綴表示 TPEx）
    - 'TW0050'   -> 元大台灣50 ETF
    - '2330'     -> 不辨識（避免與 A 股混淆）

    Args:
        code: 股票代碼（大小寫均可）

    Returns:
        True 如果是台股格式
    """
    return bool(_TW_STOCK_PATTERN.match(code.strip().upper()))


def convert_tw_stock_code(code: str) -> str:
    """
    將台股代碼轉換為 Yahoo Finance 格式。

    規則：
    - TW2330   -> 2330.TW  （上市，.TW）
    - TW6488O  -> 6488.TWO （上櫃，.TWO，O 後綴）
    - TW0050   -> 0050.TW  （ETF 上市）

    Args:
        code: 台股代碼（帶 TW 前綴）

    Returns:
        Yahoo Finance 格式代碼
    """
    upper = code.strip().upper()
    m = _TW_STOCK_PATTERN.match(upper)
    if not m:
        return code

    numeric = m.group(1)
    suffix = m.group(2)

    if suffix == _TPEx_SUFFIX:
        return f"{numeric}.TWO"
    else:
        return f"{numeric}.TW"


def get_tw_index_yf_symbol(code: str):
    """
    取得台股指數的 Yahoo Finance 代號。

    Args:
        code: 使用者輸入的台股指數代碼

    Returns:
        (yf_symbol, 中文名稱) 或 (None, None)
    """
    upper = code.strip().upper()
    TW_INDEX_MAPPING = {
        'TWII': ('^TWII', '台灣加權指數'),
        '^TWII': ('^TWII', '台灣加權指數'),
        'TPEX': ('^TPEX', '台灣櫃買指數'),
        '^TPEX': ('^TPEX', '台灣櫃買指數'),
    }
    entry = TW_INDEX_MAPPING.get(upper)
    if entry:
        return entry
    return None, None


def is_tw_index_code(code: str) -> bool:
    """判斷是否為台股指數代碼。"""
    yf_symbol, _ = get_tw_index_yf_symbol(code)
    return yf_symbol is not None


# 台股中文名稱對照表（純數字代碼 -> 中文名稱）
_TW_STOCK_NAME_MAP: dict[str, str] = {
    # 半導體
    '2330': '台積電',
    '2303': '聯電',
    '2308': '台達電',
    '2344': '華邦電',
    '2356': '英業達',
    '2379': '瑞昱',
    '2385': '群光',
    '2454': '聯發科',
    '3008': '大立光',
    '3034': '聯詠',
    '3037': '欣興',
    '3711': '日月光投控',
    '4919': '新唐',
    '5483': '中美晶',
    '6415': '矽力-KY',
    # 金融
    '2882': '國泰金',
    '2881': '富邦金',
    '2883': '開發金',
    '2884': '玉山金',
    '2885': '元大金',
    '2886': '兆豐金',
    '2887': '台新金',
    '2888': '新光金',
    '2889': '國票金',
    '2890': '永豐金',
    '2891': '中信金',
    '2892': '第一金',
    '5880': '合庫金',
    # 電子/通訊
    '2317': '鴻海',
    '2357': '華碩',
    '2382': '廣達',
    '2395': '研華',
    '2408': '南亞科',
    '2412': '中華電',
    '3045': '台灣大',
    '4904': '遠傳',
    # 傳產/民生
    '1101': '台泥',
    '1216': '統一',
    '1301': '台塑',
    '1303': '南亞',
    '1326': '台化',
    '2002': '中鋼',
    '2207': '和泰車',
    '2912': '統一超',
    # ETF
    '0050': '元大台灣50',
    '0051': '元大中型100',
    '0052': '富邦科技',
    '0056': '元大高股息',
    '00878': '國泰永續高股息',
    '006208': '富邦台50',
    '00713': '元大台灣高息低波',
}


def get_tw_stock_name(code: str) -> str | None:
    """
    根據台股代碼取得中文名稱。

    Args:
        code: 台股代碼，可帶 TW 前綴（如 'TW2330'）或純數字（如 '2330'）

    Returns:
        中文名稱，若不在對照表中則回傳 None
    """
    upper = code.strip().upper()
    # 帶 TW 前綴：取出數字部分
    m = _TW_STOCK_PATTERN.match(upper)
    if m:
        numeric = m.group(1)
    else:
        numeric = upper
    return _TW_STOCK_NAME_MAP.get(numeric)
