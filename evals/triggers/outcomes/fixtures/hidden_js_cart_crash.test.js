"use strict";
// Held-out behavior test for js-cart-crash; copied into web/tests/ only at scoring time.
const test = require("node:test");
const assert = require("node:assert/strict");
const { checkout } = require("../src/cart.js");

test("a cart with no items field checks out at zero", () => {
  assert.deepEqual(checkout({}), { totalCents: 0, lines: 0 });
});

test("an empty items list checks out at zero", () => {
  assert.deepEqual(checkout({ items: [] }), { totalCents: 0, lines: 0 });
});

test("a full cart still totals its lines", () => {
  assert.deepEqual(checkout({ items: [{ priceCents: 300, qty: 3 }] }), { totalCents: 900, lines: 1 });
});
