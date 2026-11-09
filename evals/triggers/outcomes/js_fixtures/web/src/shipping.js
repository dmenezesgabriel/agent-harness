"use strict";
// Shipping cost in cents for a parcel, by carrier.

function shippingCents(carrier, kg) {
  if (carrier === "ups") {
    return 500 + kg * 100;
  } else if (carrier === "fedex") {
    return 700 + kg * 80;
  } else if (carrier === "usps") {
    return 300 + kg * 120;
  } else {
    throw new Error("unknown carrier: " + carrier);
  }
}

module.exports = { shippingCents };
