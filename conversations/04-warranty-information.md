# Scenario 4 – Warranty Information
> **Validation note:** This is a representative dialogue manually authored from verified local tool outputs and policy retrieval results. It is not a recorded live LLM transcript. The English text is a faithful rendering of the intended Brazilian Portuguese customer-facing interaction.

**Customer:**

What is the warranty period for a musical instrument?

**Assistant:**

Our products have a 90-day legal warranty against manufacturing defects, starting from the date you receive the product.

Some manufacturers also offer additional warranties, generally ranging from six months to two years, depending on the product and the manufacturer's specific conditions.

The warranty does not cover situations such as misuse, accidental damage, or unauthorized modifications.

If you tell me which instrument you are interested in, I can help you identify the relevant warranty information.

**Technical implementation:**

The `retrieve_policy` tool retrieves the warranty sections from the policy PDF. The response distinguishes the 90-day legal warranty from additional manufacturer coverage, which varies by product.

