"use strict";
// Held-out behavior test for js-shipping-carrier; copied into web/tests/ only at scoring time.
const test = require("node:test");
const assert = require("node:assert/strict");
const { shippingCents } = require("../src/shipping.js");

test("dhl charges 900 base plus 60 per kg", () => {
  assert.equal(shippingCents("dhl", 5), 1200);
});

test("existing carriers keep their prices", () => {
  assert.equal(shippingCents("ups", 1), 600);
  assert.equal(shippingCents("fedex", 1), 780);
  assert.equal(shippingCents("usps", 1), 420);
});

test("unknown carriers are still rejected", () => {
  assert.throws(() => shippingCents("pigeon", 1), /unknown carrier/);
});
