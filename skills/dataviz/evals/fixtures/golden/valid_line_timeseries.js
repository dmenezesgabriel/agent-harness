// Valid line chart - multi-series time data with explicit colorblind-safe colors.
import Chart from "chart.js/auto";

const ctx = document.getElementById("regional-trend").getContext("2d");

new Chart(ctx, {
  type: "line",
  data: {
    labels: ["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01"],
    datasets: [
      {
        label: "Northeast",
        data: [125000, 131000, 128000, 142000],
        borderColor: "#0072B2",
        backgroundColor: "#0072B2",
      },
      {
        label: "Southeast",
        data: [98000, 92000, 87000, 89000],
        borderColor: "#E69F00",
        backgroundColor: "#E69F00",
      },
      {
        label: "Midwest",
        data: [110000, 118000, 124000, 128000],
        borderColor: "#009E73",
        backgroundColor: "#009E73",
      },
      {
        label: "West",
        data: [145000, 152000, 160000, 167000],
        borderColor: "#CC79A7",
        backgroundColor: "#CC79A7",
      },
    ],
  },
  options: {
    scales: {
      y: {
        beginAtZero: true,
      },
    },
    plugins: {
      title: {
        display: true,
        text: "Revenue trends diverge across regions over 2024",
      },
    },
  },
});
