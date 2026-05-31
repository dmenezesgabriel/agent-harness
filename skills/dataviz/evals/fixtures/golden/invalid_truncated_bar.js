// Invalid bar chart — y-axis starts at 8000 instead of zero (truncated baseline)
import Chart from "chart.js/auto";

const ctx = document.getElementById("chart").getContext("2d");

new Chart(ctx, {
  type: "bar",
  data: {
    labels: ["Q1", "Q2", "Q3", "Q4"],
    datasets: [
      {
        label: "Sales",
        data: [9200, 10500, 9800, 11000],
        backgroundColor: "#59a14f",
      },
    ],
  },
  options: {
    scales: {
      y: {
        min: 8000,
      },
    },
  },
});
