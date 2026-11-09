"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { checkout } = require("../src/cart.js");

test("checkout totals the lines", () => {
  const cart = { items: [{ priceCents: 500, qty: 2 }, { priceCents: 250, qty: 1 }] };
  assert.deepEqual(checkout(cart), { totalCents: 1250, lines: 2 });
});
