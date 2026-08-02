# -*- coding: utf-8 -*-
"""Classify each of the 100 real questions in evaluation_dataset/questions.json into one of
the eleven AEGIS analytical patterns. This is the author's own single-annotator
classification (not independently cross-checked by a second annotator), but it is tied to
the actual, published 100-query benchmark rather than an unpublished dataset. Output is a
JSON artifact mapping each question to its assigned pattern plus summary statistics, so the
classification can be independently spot-checked against evaluation_dataset/questions.json.

Each entry below pairs the exact question text with its assigned pattern, so alignment is
verified against the source file directly rather than relying on positional indices.
"""
import json

import os
_HERE = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_PATH = os.path.join(_HERE, "questions.json")
OUT_PATH = os.path.join(_HERE, "pattern_classification.json")

# (question text, assigned pattern) -- text must match questions.json exactly.
CLASSIFICATION = [
    ("What was the total revenue generated today?", "KPI"),
    ("How many orders were placed yesterday?", "KPI"),
    ("What is the average order value for the current week?", "KPI"),
    ("What was the gross profit margin for last month?", "KPI"),
    ("How many new customers signed up this morning?", "KPI"),
    ("What is the total number of refunds processed today?", "KPI"),
    ("What is the conversion rate for visitors on the homepage today?", "KPI"),
    ("How many coupons were redeemed in the past 24 hours?", "KPI"),
    ("What is the total shipping cost incurred this week?", "KPI"),
    ("What is the net revenue after discounts for today?", "KPI"),
    ("Who are the top 10 customers by total spending?", "Ranking"),
    ("Which 5 products generated the highest revenue last month?", "Ranking"),
    ("List the top 7 most frequently purchased categories this quarter.", "Ranking"),
    ("Who are the 15 customers with the highest order count in 2023?", "Ranking"),
    ("Which 8 suppliers have delivered the most items in the past year?", "Ranking"),
    ("Who are the top 5 new customers by first\u2011order value?", "Ranking"),
    ("Which 10 products have the highest profit margin this month?", "Ranking"),
    ("Identify the top 12 countries by sales volume in the last 30 days.", "Ranking"),
    ("Which 6 product bundles are purchased together most often?", "Ranking"),
    ("Who are the top 3 referral sources driving the most revenue?", "Ranking"),
    ("Show sales by month for 2023.", "Trend"),
    ("Display the daily revenue trend for the past 90 days.", "Trend"),
    ("What are the weekly order count trends for the last 6 months?", "Trend"),
    ("Show the month\u2011over\u2011month growth rate of average order value for 2022\u20112023.", "Trend"),
    ("Plot the quarterly revenue trend for each product category in 2023.", "Trend"),
    ("How have cart abandonment rates changed week over week this year?", "Trend"),
    ("Show the daily new\u2011customer acquisition trend for the past 180 days.", "Trend"),
    ("Display the trend of refunds as a percentage of sales for the last 12 months.", "Trend"),
    ("Chart the number of sold units per day for the top 5 products in the last quarter.", "Trend"),
    ("What is the trend of discount usage by month for the past year?", "Trend"),
    ("Compare sales between Electronics and Apparel.", "Comparison"),
    ("Show revenue differences between the US and Canada for Q2 2023.", "Comparison"),
    ("Contrast the average order value of first\u2011time buyers vs. returning customers.", "Cohort"),
    ("Compare the conversion rates of traffic from Google Ads vs. Facebook Ads.", "Comparison"),
    ("How do the refund rates differ between the Clothing and Home\u2011Goods categories?", "Comparison"),
    ("Contrast the monthly gross profit of the Top\u20113 selling product lines.", "Comparison"),
    ("Compare the number of orders placed on mobile versus desktop in the last 30 days.", "Comparison"),
    ("Show the difference in shipping costs between Standard and Express delivery methods.", "Comparison"),
    ("Compare the cart abandonment rate before and after the site redesign.", "Comparison"),
    ("List products with stock less than 10.", "Exception"),
    ("Which items have not been sold in the past 60 days and have inventory below 5 units?", "Exception"),
    ("Show all products that are out of stock but have pending orders.", "Exception"),
    ("Identify SKUs with a sell\u2011through rate under 20% in the last month.", "Exception"),
    ("List orders placed with invalid coupon codes in the past week.", "Exception"),
    ("Which products have a rating below 3 stars and inventory over 20?", "Exception"),
    ("Find customers whose total spend exceeds $10,000 but have no orders in the last 90 days.", "Exception"),
    ("List categories where average discount exceeds 30% this quarter.", "Exception"),
    ("Show orders with shipping delays greater than 5 days in the last month.", "Exception"),
    ("Give me an overview of product category performance.", "Summary"),
    ("Summarize total sales, average order value, and order count for each major product category this year.", "Summary"),
    ("Provide a dashboard of revenue, profit, and return rate by department for the last quarter.", "Summary"),
    ("Show a side\u2011by\u2011side summary of new vs. returning customer metrics for the past six months.", "Summary"),
    ("What is the overall health score combining sales, stock levels, and refund rates for each category?", "Summary"),
    ("Give a month\u2011by\u2011month snapshot of revenue, units sold, and discount usage for the top 5 categories.", "Summary"),
    ("Summarize the performance of each marketing campaign in terms of revenue, new customers, and conversion rate.", "Summary"),
    ("Provide a high\u2011level view of orders, revenue, and average shipping cost per payment method for the last year.", "Summary"),
    ("Show a comparative summary of sales, returns, and net profit for each sales channel (online, mobile app, marketplace).", "Summary"),
    ("How many abandoned orders were there yesterday?", "KPI"),
    ("What is the average time from order placement to shipment for orders placed this week?", "KPI"),
    ("Which 7 product tags have generated the most sales in the past 90 days?", "Ranking"),
    ("How many abandoned carts were recovered after a reminder email in the last month?", "KPI"),
    ("What is the total revenue contributed by customers who have placed more than 5 orders?", "Exception"),
    ("Which payment method has the highest failure rate during checkout today?", "Ranking"),
    ("What is the percentage of first\u2011time buyers versus repeat buyers for the current quarter?", "Cohort"),
    ("Which 5 sales promotions produced the highest ROI in the last 6 weeks?", "Ranking"),
    ("How many orders were placed using mobile devices versus desktop in the past 30 days?", "Comparison"),
    ("What is the average discount amount applied per order for the last two weeks?", "KPI"),
    ("Which 8 product variants (size/color) have the highest return rate this month?", "Ranking"),
    ("What is the total number of gift\u2011wrapped orders shipped this week?", "KPI"),
    ("How many orders included a free shipping coupon in the previous fiscal year?", "KPI"),
    ("Which 6 customer segments (e.g., age, location) generate the most cross\u2011sell revenue?", "Ranking"),
    ("What is the average number of items per order for the top\u2011selling category this quarter?", "KPI"),
    ("Which 4 referral programs have the lowest cost per acquisition over the last 12 months?", "Ranking"),
    ("How many orders were placed using a saved payment method versus a new one today?", "Comparison"),
    ("What is the total revenue from subscription\u2011based products in the last 90 days?", "KPI"),
    ("Which 5 product bundles have the highest average order value when sold together?", "Ranking"),
    ("What is the percentage of orders that required manual fraud review this week?", "KPI"),
    ("Which 3 shipping carriers delivered orders on time at a rate above 98% this month?", "Exception"),
    ("How many customers used a loyalty point redemption in their purchase today?", "KPI"),
    ("What is the average customer lifetime value for the top 10% of spenders?", "KPI"),
    ("Which 9 product categories saw a decline in sales compared to the same period last year?", "Exception"),
    ("What is the total number of orders placed through the API in the past 24 hours?", "KPI"),
    ("Which 5 marketing email campaigns generated the highest click\u2011through rate this month?", "Ranking"),
    ("How many orders were placed during peak traffic hours (6\u202fpm\u20139\u202fpm) yesterday?", "KPI"),
    ("What is the average shipping distance for orders shipped today?", "KPI"),
    ("Which 7 countries have the highest average order value for international shipments?", "Ranking"),
    ("How many orders were placed using a promotional code that expired within the last week?", "Exception"),
    ("What is the total revenue lost due to out\u2011of\u2011stock items in the last quarter?", "KPI"),
    ("Which 4 product attributes (e.g., material, brand) correlate most strongly with higher margins?", "Correlate"),
    ("How many orders were placed by customers who signed up via social media login this month?", "Exception"),
    ("What is the average number of support tickets generated per 1,000 orders this week?", "KPI"),
    ("Which 6 product pages have the highest bounce rate after view in the past 30 days?", "Ranking"),
    ("How many orders were flagged for potential duplicate payment this week?", "Exception"),
    ("What is the total number of units returned because of incorrect product descriptions?", "Exception"),
    ("Which 5 upsell offers generated the most additional revenue when presented at checkout?", "Ranking"),
    ("How many customers abandoned checkout after seeing shipping costs in the last 48 hours?", "Funnel"),
    ("What is the average rating for products that were returned more than twice?", "Exception"),
    ("Which 8 seasonal products exceeded their forecasted sales by more than 20% this year?", "Exception"),
    ("How many orders were processed using a third\u2011party marketplace integration today?", "KPI"),
    ("What is the total cost saved by automating order invoicing in the past six months?", "KPI"),
]


def main():
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        all_questions = json.load(f)

    # questions.json holds 100 in-scope queries followed by 7 deliberately
    # out-of-scope probes (see evaluation_dataset/README.md). Only the first
    # 100 are classified into one of the eleven patterns — the probes are
    # out of scope by design and intentionally excluded here.
    questions = all_questions[:len(CLASSIFICATION)]

    assert len(all_questions) >= len(CLASSIFICATION), (
        f"questions.json has fewer entries ({len(all_questions)}) than the "
        f"{len(CLASSIFICATION)} classified in-scope questions")

    for i, (q, (cq, label)) in enumerate(zip(questions, CLASSIFICATION)):
        if q != cq:
            raise ValueError(f"Text mismatch at index {i}:\n  source:  {q!r}\n  classify: {cq!r}")

    records = [{"index": i, "question": q, "pattern": label}
               for i, (q, label) in enumerate(
                   (q, lab) for q, (_, lab) in zip(questions, CLASSIFICATION))]

    counts = {}
    for _, label in CLASSIFICATION:
        counts[label] = counts.get(label, 0) + 1
    total = len(CLASSIFICATION)

    all_patterns = ["KPI", "Ranking", "Trend", "Comparison", "Exception", "Summary",
                    "Segment", "Funnel", "Cohort", "Correlate", "Tabular"]
    for p in all_patterns:
        counts.setdefault(p, 0)

    stats = {p: {"count": counts[p], "pct": round(counts[p] / total * 100, 1)}
             for p in all_patterns}

    out = {
        "source": "evaluation_dataset/questions.json",
        "method": "Single-annotator classification by the thesis author; not independently "
                  "cross-checked by a second annotator. Provided so the classification can be "
                  "spot-checked against the question text directly.",
        "total_questions": total,
        "pattern_stats": stats,
        "records": records,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"Total classified: {total}")
    for p in sorted(all_patterns, key=lambda p: -counts[p]):
        print(f"  {p:<12} {counts[p]:>3}  {stats[p]['pct']:>5.1f}%")
    print(f"Sum check: {sum(counts[p] for p in all_patterns)}")
    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
