# Scenario 1 – Product Search
> **Validation note:** This is a representative dialogue manually authored from verified local tool outputs and policy retrieval results. It is not a recorded live LLM transcript. The English text is a faithful rendering of the intended Brazilian Portuguese customer-facing interaction.

**Customer:**

What acoustic guitars do you have available for up to R$1,000?

**Assistant:**

We have several acoustic guitar options within your budget!

Here are three examples currently available:

- Tagima Memphis AC-39 Nylon Natural – R$429.90 (15 units in stock).
- Yamaha C40 Nylon Natural – R$599.90 (12 units in stock).
- Yamaha F310 Aço Natural – R$699.90 (14 units in stock).

Our catalog contains 12 matching products in total. These are some of the available options.

Would you like help comparing their specifications and choosing the best instrument for your needs?

**Technical implementation:**

The `search_products` tool retrieves products using category and maximum-price filters. The information above comes from local catalog validation.

