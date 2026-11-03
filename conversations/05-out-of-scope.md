# Scenario 5 – Out-of-Scope Request
> **Validation note:** This is a representative dialogue manually authored from verified local tool outputs and policy retrieval results. It is not a recorded live LLM transcript. The English text is a faithful rendering of the intended Brazilian Portuguese customer-facing interaction.

**Customer:**

Can you teach me how to prepare a chocolate cake?

**Assistant:**

I'm here to help you with musical instruments, products, orders, and Empório da Música policies.

I may not be the best assistant for cooking recipes, but I'd be happy to help you find an instrument or answer any questions about our store!

**Technical implementation:**

The policy retrieval validation for an unrelated chocolate cake query returned `no_relevant_context`. This example illustrates the intended out-of-scope response. The exact live Gemini response was not validated because the API free-tier daily quota had been exhausted.

