"""Prompt templates for LLM-based categorical estimation.

Extracted from Parallax 010_categorical_convergence.py.
Configurable: entity_noun, value_noun, extra_instructions.
"""


DEFAULT_TEMPLATE = """For each {entity_noun} below, classify its {axis_description}.

{ubl_prompt}

Output format: {entity_noun},{value_noun}
({value_noun} must be EXACTLY one of: {enum_list})

IMPORTANT:
- Choose the SINGLE best-fitting category
- Do NOT output numbers or scores — only the enum value
- If genuinely uncertain, pick the closest match
- Consider how the {entity_noun} is actually USED in everyday context, not its dictionary definition
{extra_instructions}

{entity_noun_cap}s:
{entity_list}

Output ONLY the {entity_noun},{value_noun} pairs. No explanations. One per line."""


class PromptTemplate:
    """Configurable prompt template for categorical estimation."""

    def __init__(
        self,
        *,
        template: str | None = None,
        entity_noun: str = "word",
        value_noun: str = "value",
        extra_instructions: str = "",
    ):
        self.template = template or DEFAULT_TEMPLATE
        self.entity_noun = entity_noun
        self.value_noun = value_noun
        self.extra_instructions = extra_instructions

    def generate(
        self,
        axis_description: str,
        ubl_prompt: str,
        enum_values: list[str],
        entities: list[str],
    ) -> str:
        """Generate an estimation prompt.

        Args:
            axis_description: what the axis measures
            ubl_prompt: usage-based framing for the axis
            enum_values: valid enum value strings
            entities: list of entities to classify
        """
        extra = ""
        if self.extra_instructions:
            extra = f"\n{self.extra_instructions}"

        return self.template.format(
            entity_noun=self.entity_noun,
            entity_noun_cap=self.entity_noun.capitalize(),
            value_noun=self.value_noun,
            axis_description=axis_description,
            ubl_prompt=ubl_prompt,
            enum_list=", ".join(enum_values),
            entity_list="\n".join(entities),
            extra_instructions=extra,
        )
