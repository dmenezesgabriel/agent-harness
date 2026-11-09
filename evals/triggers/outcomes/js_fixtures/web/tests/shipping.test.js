"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { shippingCents } = require("../src/shipping.js");

test("ups charges base plus per kg", () => {
  assert.equal(shippingCents("ups", 2), 700);
});

test("unknown carrier is rejected", () => {
  assert.throws(() => shippingCents("pigeon", 1), /unknown carrier: pigeon/);
});
