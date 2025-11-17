# Optimal Model Configuration for Extraction

**Date**: 2025-11-16
**Purpose**: Configure optimal round-robin and fallback chains with multiple API providers
**Goal**: Maximize extraction quality while avoiding rate limits and minimizing cost

---

## 🎯 Extraction Requirements

### Task Characteristics
- **Type**: Structured entity extraction from Spanish interviews
- **Language**: Spanish (not all models handle well)
- **Format**: JSON object output (must follow schema)
- **Volume**: 44 interviews × 17 extractors = 748 API calls
- **Duration**: 40-60 minutes (need consistent availability)
- **Budget**: $2-5 USD target

### Quality Requirements
- **Accuracy**: Must extract Spanish entities correctly
- **Schema adherence**: Must follow JSON format exactly
- **Consistency**: Similar results across interviews
- **UTF-8 handling**: Must preserve Spanish characters (á, é, í, ó, ú, ñ)

---

## 📊 Model Analysis

### OpenAI Models

**gpt-4o-mini** ⭐⭐⭐⭐⭐
- **Cost**: $0.15/1M input, $0.60/1M output (~$0.01 per interview)
- **Speed**: Fast (2-5 seconds per call)
- **Spanish**: Excellent
- **JSON**: Excellent with `response_format={"type": "json_object"}`
- **Rate limit**: 500 RPM (10,000 TPM)
- **Recommendation**: **PRIMARY MODEL** - Best cost/quality balance

**gpt-4o** ⭐⭐⭐⭐
- **Cost**: $2.50/1M input, $10/1M output (~$0.10 per interview)
- **Speed**: Medium (3-7 seconds per call)
- **Spanish**: Excellent
- **JSON**: Excellent
- **Rate limit**: 500 RPM (30,000 TPM)
- **Recommendation**: **FALLBACK** - High quality but expensive

**o1-mini** ⭐⭐⭐
- **Cost**: $3/1M input, $12/1M output (~$0.12 per interview)
- **Speed**: Slow (10-30 seconds per call)
- **Spanish**: Good
- **JSON**: Good but slower reasoning
- **Rate limit**: 50 RPM (2,000,000 TPM)
- **Recommendation**: **LAST RESORT** - Slow but high reasoning capability

**gpt-3.5-turbo** ⭐⭐
- **Cost**: $0.50/1M input, $1.50/1M output (~$0.005 per interview)
- **Speed**: Very fast (1-3 seconds)
- **Spanish**: Good
- **JSON**: Acceptable
- **Rate limit**: 500 RPM (10,000 TPM)
- **Recommendation**: **EMERGENCY FALLBACK** - Cheap but lower quality

### Google Gemini Models

**gemini-1.5-flash** ⭐⭐⭐⭐⭐
- **Cost**: $0.075/1M input, $0.30/1M output (~$0.005 per interview)
- **Speed**: Very fast (1-3 seconds)
- **Spanish**: Excellent
- **JSON**: Excellent
- **Rate limit**: 1,000 RPM (4M TPM)
- **Recommendation**: **PRIMARY ALTERNATIVE** - Fastest + cheapest

**gemini-1.5-pro** ⭐⭐⭐⭐
- **Cost**: $1.25/1M input, $5/1M output (~$0.06 per interview)
- **Speed**: Medium (3-6 seconds)
- **Spanish**: Excellent
- **JSON**: Excellent
- **Rate limit**: 1,000 RPM (4M TPM)
- **Recommendation**: **HIGH-QUALITY FALLBACK** - Better reasoning

**gemini-2.0-flash-exp** ⭐⭐⭐⭐⭐
- **Cost**: FREE during preview
- **Speed**: Very fast (1-3 seconds)
- **Spanish**: Excellent (improved multilingual)
- **JSON**: Excellent
- **Rate limit**: 1,000 RPM (4M TPM)
- **Recommendation**: **BEST VALUE** - Free + fast + high quality

### DeepSeek Models

**deepseek-chat** (DeepSeek-V3) ⭐⭐⭐⭐
- **Cost**: $0.27/1M input, $1.10/1M output (~$0.007 per interview)
- **Speed**: Fast (2-4 seconds)
- **Spanish**: Good (improving)
- **JSON**: Good
- **Rate limit**: Varies by tier
- **Recommendation**: **BUDGET ALTERNATIVE** - Good quality, low cost

**deepseek-reasoner** ⭐⭐⭐
- **Cost**: $0.55/1M input, $2.19/1M output (~$0.015 per interview)
- **Speed**: Slow (5-15 seconds, reasoning tokens)
- **Spanish**: Good
- **JSON**: Excellent
- **Rate limit**: Varies by tier
- **Recommendation**: **SKIP** - Overkill for extraction, slow

### K2 Models (Anthropic Claude via K2)

**Note**: K2 is not a model provider - you might mean:
- **Anthropic Claude** (claude-3-5-sonnet, claude-3-haiku)
- **Cohere** (command-r, command-r-plus)
- **Mistral** (mistral-large, mistral-medium)

**Assuming K2 = Anthropic Claude**:

**claude-3-5-sonnet-20241022** ⭐⭐⭐⭐⭐
- **Cost**: $3/1M input, $15/1M output (~$0.12 per interview)
- **Speed**: Medium (3-7 seconds)
- **Spanish**: Excellent
- **JSON**: Excellent
- **Rate limit**: Varies by tier
- **Recommendation**: **HIGH-QUALITY FALLBACK** - Best reasoning

**claude-3-haiku-20240307** ⭐⭐⭐⭐
- **Cost**: $0.25/1M input, $1.25/1M output (~$0.008 per interview)
- **Speed**: Very fast (1-3 seconds)
- **Spanish**: Excellent
- **JSON**: Excellent
- **Rate limit**: Varies by tier
- **Recommendation**: **FAST FALLBACK** - Good balance

---

## 🏆 Recommended Configuration

### Strategy 1: Cost-Optimized (Recommended for 44 interviews)

**Objective**: Minimize cost while maintaining quality

```json
{
  "model_routing": {
    "round_robin": [
      "gemini-2.0-flash-exp",    // FREE, fast, excellent
      "gemini-1.5-flash",        // $0.005, very fast
      "gpt-4o-mini",             // $0.01, fast, reliable
      "deepseek-chat",           // $0.007, fast
      "claude-3-haiku"           // $0.008, fast fallback
    ],
    "fallback": [
      "gemini-2.0-flash-exp",    // First attempt
      "gpt-4o-mini",             // If Gemini fails
      "gemini-1.5-flash",        // If OpenAI rate limited
      "deepseek-chat",           // Budget alternative
      "claude-3-haiku",          // Fast Claude
      "gpt-4o",                  // High quality
      "gemini-1.5-pro",          // Gemini high quality
      "claude-3-5-sonnet",       // Best reasoning
      "o1-mini"                  // Last resort
    ],
    "providers": {
      "gemini-2.0-flash-exp": {"provider": "gemini"},
      "gemini-1.5-flash": {"provider": "gemini"},
      "gemini-1.5-pro": {"provider": "gemini"},
      "gpt-4o-mini": {"provider": "openai"},
      "gpt-4o": {"provider": "openai"},
      "o1-mini": {"provider": "openai"},
      "deepseek-chat": {"provider": "deepseek"},
      "claude-3-5-sonnet": {"provider": "anthropic"},
      "claude-3-haiku": {"provider": "anthropic"}
    }
  }
}
```

**Expected Cost**: $0.22 - $0.44 (44 interviews)
**Expected Duration**: 35-50 minutes
**Quality**: Excellent (Gemini 2.0 Flash Exp is very good)

---

### Strategy 2: Quality-Optimized (For critical extractions)

**Objective**: Maximum quality, cost secondary

```json
{
  "model_routing": {
    "round_robin": [
      "gpt-4o-mini",             // Proven reliable
      "claude-3-5-sonnet",       // Best reasoning
      "gemini-1.5-pro",          // High quality Gemini
      "gpt-4o"                   // OpenAI flagship
    ],
    "fallback": [
      "claude-3-5-sonnet",       // First attempt
      "gpt-4o",                  // If Claude fails
      "gemini-1.5-pro",          // If OpenAI rate limited
      "gpt-4o-mini",             // Reliable fallback
      "claude-3-haiku",          // Fast Claude
      "gemini-2.0-flash-exp",    // Free quality
      "o1-mini"                  // Deep reasoning
    ],
    "providers": {
      "claude-3-5-sonnet": {"provider": "anthropic"},
      "claude-3-haiku": {"provider": "anthropic"},
      "gpt-4o-mini": {"provider": "openai"},
      "gpt-4o": {"provider": "openai"},
      "o1-mini": {"provider": "openai"},
      "gemini-1.5-pro": {"provider": "gemini"},
      "gemini-2.0-flash-exp": {"provider": "gemini"}
    }
  }
}
```

**Expected Cost**: $4.40 - $8.80 (44 interviews)
**Expected Duration**: 40-60 minutes
**Quality**: Maximum

---

### Strategy 3: Speed-Optimized (Fast iteration)

**Objective**: Fastest extraction for testing

```json
{
  "model_routing": {
    "round_robin": [
      "gemini-1.5-flash",        // Very fast
      "gemini-2.0-flash-exp",    // Very fast + free
      "claude-3-haiku",          // Very fast
      "gpt-4o-mini"              // Fast
    ],
    "fallback": [
      "gemini-1.5-flash",
      "gemini-2.0-flash-exp",
      "claude-3-haiku",
      "gpt-4o-mini",
      "deepseek-chat",
      "gpt-4o"
    ],
    "providers": {
      "gemini-1.5-flash": {"provider": "gemini"},
      "gemini-2.0-flash-exp": {"provider": "gemini"},
      "claude-3-haiku": {"provider": "anthropic"},
      "gpt-4o-mini": {"provider": "openai"},
      "gpt-4o": {"provider": "openai"},
      "deepseek-chat": {"provider": "deepseek"}
    }
  }
}
```

**Expected Cost**: $0.22 - $0.66 (44 interviews)
**Expected Duration**: 25-40 minutes
**Quality**: Good

---

## 🔧 Implementation

### Step 1: Update .env

```bash
# OpenAI (already configured)
OPENAI_API_KEY=sk-...

# Gemini (NEW - recommended!)
GEMINI_API_KEY=your_gemini_api_key_here

# DeepSeek (NEW - budget option)
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Anthropic (NEW - high quality)
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Mistral, Cohere if needed
MISTRAL_API_KEY=your_mistral_api_key_here
COHERE_API_KEY=your_cohere_api_key_here
```

### Step 2: Get API Keys

**Gemini** (Recommended - best value):
```bash
# Get free API key from Google AI Studio
# https://aistudio.google.com/app/apikey

# Free tier: 15 RPM, 1M TPM (enough for testing)
# Paid tier: 1,000 RPM, 4M TPM
```

**DeepSeek** (Budget option):
```bash
# Get API key from DeepSeek Platform
# https://platform.deepseek.com/

# Free tier: 60 RPM
# Paid tier: Higher limits
```

**Anthropic** (High quality):
```bash
# Get API key from Anthropic Console
# https://console.anthropic.com/

# $5 minimum credit purchase
```

### Step 3: Update Config

Replace `config/extraction_config.json` model_routing section with **Strategy 1** (recommended):

```json
{
  "model_routing": {
    "round_robin": [
      "gemini-2.0-flash-exp",
      "gemini-1.5-flash",
      "gpt-4o-mini",
      "deepseek-chat",
      "claude-3-haiku"
    ],
    "fallback": [
      "gemini-2.0-flash-exp",
      "gpt-4o-mini",
      "gemini-1.5-flash",
      "deepseek-chat",
      "claude-3-haiku",
      "gpt-4o",
      "gemini-1.5-pro",
      "claude-3-5-sonnet",
      "o1-mini"
    ],
    "providers": {
      "gemini-2.0-flash-exp": {"provider": "gemini"},
      "gemini-1.5-flash": {"provider": "gemini"},
      "gemini-1.5-pro": {"provider": "gemini"},
      "gpt-4o-mini": {"provider": "openai"},
      "gpt-4o": {"provider": "openai"},
      "o1-mini": {"provider": "openai"},
      "deepseek-chat": {"provider": "deepseek"},
      "deepseek-reasoner": {"provider": "deepseek"},
      "claude-3-5-sonnet": {"provider": "anthropic"},
      "claude-3-haiku": {"provider": "anthropic"}
    }
  }
}
```

### Step 4: Implement Provider Support

**File**: `intelligence_capture/model_router.py`

Need to add Gemini, DeepSeek, Anthropic client initialization:

```python
# Add imports
from anthropic import Anthropic
import google.generativeai as genai
# DeepSeek uses OpenAI-compatible API

# In call_llm_with_fallback()
def get_client_for_provider(provider: str):
    """Get appropriate client for provider"""
    if provider == "openai":
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    elif provider == "anthropic":
        return Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    elif provider == "gemini":
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        return genai
    elif provider == "deepseek":
        # DeepSeek uses OpenAI-compatible API
        return OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com/v1"
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")
```

---

## 📊 Cost Comparison

### Per Interview Cost (17 extractors)

| Model | Cost per Interview | 44 Interviews Total |
|-------|-------------------|---------------------|
| gemini-2.0-flash-exp | **$0.00** | **$0.00** |
| gemini-1.5-flash | $0.005 | $0.22 |
| gpt-4o-mini | $0.01 | $0.44 |
| deepseek-chat | $0.007 | $0.31 |
| claude-3-haiku | $0.008 | $0.35 |
| gpt-4o | $0.10 | $4.40 |
| claude-3-5-sonnet | $0.12 | $5.28 |
| o1-mini | $0.12 | $5.28 |

### Strategy Cost Summary

| Strategy | Total Cost (44 interviews) | Duration | Quality |
|----------|---------------------------|----------|---------|
| **Cost-Optimized** | $0.22 - $0.44 | 35-50 min | ⭐⭐⭐⭐⭐ |
| **Quality-Optimized** | $4.40 - $8.80 | 40-60 min | ⭐⭐⭐⭐⭐ |
| **Speed-Optimized** | $0.22 - $0.66 | 25-40 min | ⭐⭐⭐⭐ |

---

## 🎯 Recommendation

### For Full 44-Interview Run: **Cost-Optimized Strategy**

**Why**:
1. **Gemini 2.0 Flash Exp** is FREE and excellent quality
2. **95% cost savings** vs current gpt-4o-mini primary
3. **Higher rate limits** (1,000 RPM vs 500 RPM)
4. **Faster** (1-3s vs 2-5s per call)
5. **Multiple fallbacks** prevent rate limit issues

**Primary**: gemini-2.0-flash-exp (free, fast, excellent)
**Fallback**: gpt-4o-mini (proven reliable)
**Emergency**: Full 9-model fallback chain

**Expected result**:
- Cost: $0.00 - $0.44 (vs $0.44 - $4.40 current)
- Duration: 35-50 minutes (vs 40-60 current)
- Quality: Same or better (Gemini 2.0 is very good)

---

## ✅ Next Steps

1. **Get API keys** (15 minutes):
   - ✅ Gemini: https://aistudio.google.com/app/apikey (FREE)
   - ⏳ DeepSeek: https://platform.deepseek.com/ (optional)
   - ⏳ Anthropic: https://console.anthropic.com/ (optional)

2. **Update .env** (2 minutes):
   ```bash
   # Add to .env
   GEMINI_API_KEY=your_key_here
   DEEPSEEK_API_KEY=your_key_here  # optional
   ANTHROPIC_API_KEY=your_key_here  # optional
   ```

3. **Update config** (2 minutes):
   - Replace model_routing in `config/extraction_config.json`

4. **Implement provider support** (15 minutes):
   - Update `intelligence_capture/model_router.py`
   - Add Gemini, DeepSeek, Anthropic clients

5. **Test with single interview** (2 minutes):
   ```bash
   python3 scripts/test_single_interview.py
   ```

6. **Run full pipeline** (35-50 minutes):
   ```bash
   python3 intelligence_capture/run.py
   ```

---

**Total setup time**: ~30 minutes
**Total savings**: $0.44 - $4.40 → $0.00 - $0.44 (90-100% cost reduction!)
**Quality**: Same or better

**Recommendation**: Get Gemini API key (free), implement provider support, run with cost-optimized strategy! 🚀
