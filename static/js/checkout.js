(function () {
  const form = document.getElementById("checkout-form");
  if (!form) {
    return;
  }

  const statusEl = document.getElementById("checkout-status");
  const submitBtn = document.getElementById("checkout-submit-btn");
  const spinner = submitBtn?.querySelector(".spinner-border");
  const defaultLabel = submitBtn?.querySelector(".default-label");
  const paymentRadios = form.querySelectorAll('input[name="payment_method"]');
  const stripeCardWrapper = document.getElementById("stripe-card-wrapper");
  const stripeKey =
    document.querySelector('meta[name="stripe-public-key"]')?.content || "";
  let stripeInstance = null;
  let cardElement = null;

  const razorpayKey =
    document.querySelector('meta[name="razorpay-key"]')?.content || "";

  if (stripeKey && window.Stripe) {
    stripeInstance = window.Stripe(stripeKey);
    const elements = stripeInstance.elements();
    cardElement = elements.create("card");
    cardElement.mount("#card-element");
    cardElement.on("change", (event) => {
      const errorEl = document.getElementById("card-errors");
      if (errorEl) {
        errorEl.textContent = event.error ? event.error.message : "";
      }
    });
  }

  const toggleStripeSection = () => {
    const method = form.querySelector(
      'input[name="payment_method"]:checked'
    )?.value;
    if (!stripeCardWrapper) return;
    if (method === "stripe" && stripeInstance) {
      stripeCardWrapper.classList.remove("d-none");
    } else {
      stripeCardWrapper.classList.add("d-none");
    }
  };

  paymentRadios.forEach((radio) =>
    radio.addEventListener("change", toggleStripeSection)
  );
  toggleStripeSection();

  const setStatus = (type, message) => {
    if (!statusEl) return;
    statusEl.className = `alert alert-${type}`;
    statusEl.textContent = message;
  };

  const setLoading = (isLoading) => {
    if (!submitBtn) return;
    submitBtn.disabled = isLoading;
    if (spinner && defaultLabel) {
      spinner.classList.toggle("d-none", !isLoading);
      defaultLabel.classList.toggle("d-none", isLoading);
    }
  };

  const csrfToken =
    form.querySelector('input[name="csrfmiddlewaretoken"]')?.value || "";

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) {
      return;
    }
    setStatus("info", "Processing order...");
    setLoading(true);

    try {
      const response = await fetch(form.dataset.checkoutEndpoint, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
          "X-Requested-With": "XMLHttpRequest",
        },
        body: new FormData(form),
      });
      if (!response.ok) {
        throw new Error("Unable to create order. Please try again.");
      }
      const data = await response.json();
      await handlePaymentFlow(data);
    } catch (error) {
      console.error(error);
      setStatus("danger", error.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  });

  async function handlePaymentFlow(payload) {
    switch (payload.provider) {
      case "stripe":
        if (!stripeInstance || !cardElement) {
          throw new Error("Stripe is not ready. Check publishable key.");
        }
        const result = await stripeInstance.confirmCardPayment(
          payload.client_secret,
          {
            payment_method: {
              card: cardElement,
            },
          }
        );
        if (result.error) {
          throw new Error(result.error.message);
        }
        setStatus(
          "success",
          "Payment complete! We’ll send an email confirmation shortly."
        );
        break;
      case "razorpay":
        if (!window.Razorpay) {
          throw new Error("Razorpay script missing.");
        }
        const options = {
          key: payload.key_id || razorpayKey,
          amount: payload.amount,
          currency: payload.currency,
          order_id: payload.order_id,
          name: "Payment",
          description: "Complete your payment",
          handler: function () {
            setStatus(
              "success",
              "Razorpay payment initiated. We’ll confirm once the gateway notifies us."
            );
          },
          theme: { color: "#0d6efd" },
        };
        const rzp = new window.Razorpay(options);
        rzp.on("payment.failed", function (response) {
          setStatus("danger", response.error.description || "Payment failed.");
        });
        rzp.open();
        break;
      default:
        setStatus(
          "success",
          "Order placed with Cash on Delivery. Expect a confirmation email soon."
        );
    }
  }
})();

