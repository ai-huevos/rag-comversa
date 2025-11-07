# LLM Fallback System

## Overview

The Intelligence Capture System now includes an intelligent LLM fallback mechanism that automatically switches between different OpenAI models when rate limits are encountered. This ensures extraction continues even when one model hits its rate limit.

## How It Works

### Model Fallback Chain

When an LLM call is made, the system tries models in this order:

1. **gpt-4o-mini** (Primary)
   - Fast and cost-effective
   - Best for most extraction tasks
   - Lower rate limits

2. **gpt-4o** (Fallback 1)
   - More capacity
   - Higher rate limits
   - Different rate limit pool

3. **gpt-4-turbo** (Fallback 2)
   - Stable turbo model
   - Good for complex extractions
   - Alternative rate limits

4. **gpt-3.5-turbo** (Fallback 3)
   - Older but reliable
   - Separate rate limit pool
   - Very cost-effective

5. **gpt-4** (Fallback 4)
   - Original GPT-4
   - Different quota pool
   - High quality

6. **gpt-3.5-turbo-16k** (Fallback 5)
   - Larger context window
   - Last resort option

### Retry Logic

For each model, the system:
- **Attempts up to 3 times** before moving to the next model
- **Waits for short rate limits** (< 60 seconds) automatically
- **Switches models** for longer rate limits or quota issues
- **Uses exponential backoff** for non-rate-limit errors

### Smart Wait Times

The system intelligently handles different types of rate limits:

```python
# Short rate limit (< 60s): Wait and retry same model
"Please try again in 20s" → Waits 21s, retries same model

# Long rate limit (> 60s): Switch to next model
"Please try again in 8h46m36s" → Immediately tries next model

# Quota exceeded: Switch to next model
"You exceeded your current quota" → Immediately tries next model
```

## Usage

### Automatic (Recommended)

All extractors automatically use the fallback system. No code changes needed:

```python
from intelligence_capture.extractors import SystemExtractor

extractor = SystemExtractor()
systems = extractor.extract_from_interview(interview_data)
# Automatically handles rate limits and switches models
```

### Manual (Advanced)

You can also use the fallback function directly:

```python
from intelligence_capture.extractors import call_llm_with_fallback
from openai import OpenAI

client = OpenAI()
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Extract data from this text..."}
]

response = call_llm_with_fallback(
    client=client,
    messages=messages,
    temperature=0.1,
    max_retries=3
)
```

## Benefits

### 1. Resilience
- **No manual intervention** needed when rate limits hit
- **Automatic recovery** from temporary issues
- **Graceful degradation** through model chain

### 2. Cost Optimization
- **Starts with cheapest model** (gpt-4o-mini)
- **Only uses expensive models** when necessary
- **Minimizes API costs** while maintaining reliability

### 3. Reliability
- **Multiple fallback options** ensure extraction completes
- **Smart retry logic** handles transient errors
- **Detailed logging** for debugging

### 4. Performance
- **Short waits handled automatically** (< 60s)
- **Long waits trigger immediate fallback** (> 60s)
- **Exponential backoff** prevents API hammering

## Logging

The system provides detailed logging of fallback behavior:

```
  Attempting with model: gpt-4o-mini (attempt 1/3)
  ⚠️  Rate limit on gpt-4o-mini: Error code: 429...
  → Switching to next model in fallback chain
  
  Attempting with model: gpt-4o (attempt 1/3)
  ✓ Success with gpt-4o
```

## Error Handling

### All Models Fail

If all models in the fallback chain fail:

```python
response = call_llm_with_fallback(client, messages)
# Returns: None

# Extractors handle this gracefully:
systems = extractor.extract_from_interview(interview_data)
# Returns: [] (empty list)
```

### Partial Success

If some extractions succeed and others fail:
- Successful extractions are returned
- Failed extractions return empty lists
- No exceptions are raised
- Warnings are logged

## Configuration

### Custom Model Chain

You can customize the fallback chain by modifying `MODEL_FALLBACK_CHAIN`:

```python
# In intelligence_capture/extractors.py
MODEL_FALLBACK_CHAIN = [
    "gpt-4o-mini",
    "gpt-4o",
    "your-custom-model",
    "gpt-3.5-turbo",
]
```

### Custom Retry Count

Adjust max retries per model:

```python
response = call_llm_with_fallback(
    client=client,
    messages=messages,
    max_retries=5  # Try each model up to 5 times
)
```

## Testing

Test the fallback system:

```bash
python tests/test_llm_fallback.py
```

This will:
- Test all extractors with fallback logic
- Show which models are tried
- Display success/failure for each model
- Verify graceful handling of rate limits

## Best Practices

### 1. Monitor Costs
- Check which models are being used most
- Adjust fallback chain if costs are too high
- Consider removing expensive models if not needed

### 2. Rate Limit Management
- Add payment method to increase rate limits
- Use batch processing to stay within limits
- Schedule extractions during off-peak hours

### 3. Error Monitoring
- Review logs for frequent fallbacks
- Investigate if always falling back to expensive models
- Check for quota issues

### 4. Performance Optimization
- If always hitting rate limits, consider:
  - Upgrading OpenAI plan
  - Reducing extraction frequency
  - Batching requests more efficiently
  - Using caching for repeated extractions

## Troubleshooting

### Issue: Always falling back to expensive models

**Solution:**
- Increase rate limits by upgrading OpenAI plan
- Reduce extraction frequency
- Add delays between extractions

### Issue: All models failing

**Possible causes:**
- Quota exceeded on all models
- API key invalid
- Network issues

**Solution:**
- Check OpenAI account status
- Verify API key is valid
- Check network connectivity
- Review OpenAI billing

### Issue: Slow extractions

**Cause:** Waiting for rate limit resets

**Solution:**
- Upgrade OpenAI plan for higher limits
- Use batch processing with delays
- Schedule extractions during off-peak hours

## Implementation Details

### Function Signature

```python
def call_llm_with_fallback(
    client: OpenAI,
    messages: List[Dict],
    temperature: float = 0.1,
    max_retries: int = 3
) -> Optional[str]:
    """
    Call LLM with automatic model fallback on rate limits
    
    Args:
        client: OpenAI client instance
        messages: List of message dicts (system, user, assistant)
        temperature: Temperature for generation (0.0-2.0)
        max_retries: Max retries per model before switching
        
    Returns:
        Response content string or None if all models fail
    """
```

### Error Types Handled

- **RateLimitError**: Switches to next model or waits
- **APIError**: Retries with exponential backoff
- **Timeout**: Retries with exponential backoff
- **Connection errors**: Retries with exponential backoff
- **Other exceptions**: Logged and retried

## Future Enhancements

Potential improvements:

1. **Dynamic model selection** based on task complexity
2. **Cost tracking** per extraction
3. **Performance metrics** per model
4. **Automatic model chain optimization** based on success rates
5. **Parallel requests** to multiple models
6. **Caching** of common extractions
7. **Local model fallback** for offline operation

## Related Documentation

- [Extraction System Overview](./EXTRACTION_SYSTEM.md)
- [API Rate Limits](https://platform.openai.com/docs/guides/rate-limits)
- [OpenAI Models](https://platform.openai.com/docs/models)
