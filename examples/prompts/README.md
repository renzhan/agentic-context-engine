# Prompt Comparison Examples

Examples comparing different ACE prompt versions to understand improvements and choose the right version.

## Files

### [compare_v1_v2_prompts.py](compare_v1_v2_prompts.py)
**Compare v1.0 vs v2.0 prompts**

Shows improvements from v1.0 (simple) to v2.0 (enhanced):
- Structured output formatting
- Better error handling
- Clearer instructions

**Run:**
```bash
python compare_v1_v2_prompts.py
```

### [compare_v2_v2_1_prompts.py](compare_v2_v2_1_prompts.py)
**Compare v2.0 vs v2.1 prompts** (recommended)

Shows latest improvements in v2.1:
- MCP-inspired techniques (CRITICAL, MANDATORY keywords)
- Quick reference headers
- Explicit trigger conditions
- Atomicity scoring
- Visual indicators

**Run:**
```bash
python compare_v2_v2_1_prompts.py
```

**Benchmark result:** v2.1 shows +17% success rate vs v1.0

### [advanced_prompts_v2.py](advanced_prompts_v2.py)
**Advanced prompt engineering techniques**

Demonstrates:
- Custom prompt templates
- Role-specific customization
- Retry prompt configuration
- Multilingual support

## Which Version Should I Use?

**For production:** Use **v2.1** (latest, best performance)
```python
from ace.prompts_v2_1 import PromptManager

prompt_mgr = PromptManager()
generator = Generator(llm, prompt_template=prompt_mgr.get_generator_prompt())
reflector = Reflector(llm, prompt_template=prompt_mgr.get_reflector_prompt())
curator = Curator(llm, prompt_template=prompt_mgr.get_curator_prompt())
```

**For learning/tutorials:** v1.0 is simpler (default)
```python
from ace import Generator, Reflector, Curator

# Uses v1.0 prompts by default
generator = Generator(llm)
reflector = Reflector(llm)
curator = Curator(llm)
```

## See Also

- [Prompt Engineering Guide](../../docs/PROMPT_ENGINEERING.md) - Advanced techniques
- [Main Examples](../) - All ACE examples
- [API Reference](../../docs/API_REFERENCE.md) - Prompt configuration options
