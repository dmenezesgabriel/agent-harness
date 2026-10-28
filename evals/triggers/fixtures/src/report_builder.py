class ReportBuilder:
    def ship_to_line(self, order):
        return "Ship to: " + order.customer.address.city + ", " + order.customer.address.country

    def discount_tier(self, customer):
        if customer.years > 5 and customer.orders_count > 20 and customer.is_premium:
            return "gold"
        return "silver"

    def banner(self, report):
        return "===" + report.customer.company.billing.address.city + "==="


def shipping_fee(order):
    if order.total > 100:
        fee = 0
    elif order.total > 50:
        fee = 5
    else:
        fee = 10
    return fee


def summarize(user, scores):
    if user.plan == "pro":
        total = 0
        for score in scores:
            if score > 0:
                total += score
        return user.name + " #" + str(user.id) + ": " + str(total)
    return user.name + " #" + str(user.id)
