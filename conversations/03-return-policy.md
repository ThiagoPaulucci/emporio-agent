# Scenario 3 – Return Policy
> **Validation note:** This is a representative dialogue manually authored from verified local tool outputs and policy retrieval results. It is not a recorded live LLM transcript. The English text is a faithful rendering of the intended Brazilian Portuguese customer-facing interaction.

**Customer:**

Can I return a guitar if I change my mind?

**Assistant:**

Yes. According to our return policy, you may request a return within seven calendar days after receiving your product.

The product must be returned in its original packaging, without signs of use, and with its accessories and manuals.

The refund is processed using the original payment method within up to ten business days. Return shipping is paid by the store.

Would you like help understanding the return procedure?

**Technical implementation:**

The `retrieve_policy` tool retrieves the relevant passages from the policy PDF. The information is based on the return policy section on page 4.

