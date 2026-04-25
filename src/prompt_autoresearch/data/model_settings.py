from enum import StrEnum


class ModelString(StrEnum):
    GPT_5_4 = "gpt-5.4"
    OPUS_4_6 = "claude-opus-4-6"
    SONNET_4_6 = "claude-sonnet-4-6"
    OPUS_4_7 = "claude-opus-4-7"
    GEMINI_3_1_PRO = "gemini/gemini-3.1-pro-preview"


class ModelEffort(StrEnum):
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"
