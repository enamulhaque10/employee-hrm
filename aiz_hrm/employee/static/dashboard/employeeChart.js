$(document).ready(function () {
    function employeeChart(dataSet, labels) {
        const data = {
            labels: labels,
            datasets: dataSet,
        };
        // Create chart using the Chart.js library
        window["myChart"] = {};
        if (document.getElementById("totalEmployees")) {
            const ctx = document.getElementById("totalEmployees").getContext("2d");
            employeeChart = new Chart(ctx, {
                type: "doughnut",
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: (e, activeEls) => {
                        let datasetIndex = activeEls[0].datasetIndex;
                        let dataIndex = activeEls[0].index;
                        let datasetLabel = e.chart.data.datasets[datasetIndex].label;
                        let value = e.chart.data.datasets[datasetIndex].data[dataIndex];
                        let label = e.chart.data.labels[dataIndex];
                        var active = "False";
                        if (label.toLowerCase() == "active") {
                            active = "True";
                        }
                        localStorage.removeItem("savedFilters");
                        window.location.href = "/employee/employee-view?is_active=" + active;
                    },
                },
                plugins: [
                    {
                        afterRender: (chart) => emptyChart(chart),
                    },
                ],
            });
        }
    }

    function genderChart(dataSet, labels) {
        const data = {
            labels: labels,
            datasets: dataSet,
        };
        // Create chart using the Chart.js library
        window["genderChart"] = {};
        if (document.getElementById("genderChart")) {
            const ctx = document.getElementById("genderChart").getContext("2d");
            genderChart = new Chart(ctx, {
                type: "doughnut",
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: (e, activeEls) => {
                        let datasetIndex = activeEls[0].datasetIndex;
                        let dataIndex = activeEls[0].index;
                        let datasetLabel = e.chart.data.datasets[datasetIndex].label;
                        let value = e.chart.data.datasets[datasetIndex].data[dataIndex];
                        let label = e.chart.data.labels[dataIndex];
                        localStorage.removeItem("savedFilters");
                        window.location.href =
                            "/employee/employee-view?gender=" + label.toLowerCase();
                    },
                },
                plugins: [
                    {
                        afterRender: (chart) => emptyChart(chart),
                    },
                ],
            });
        }
    }

    function religionChart(dataSet, labels) {
        const data = {
            labels: labels,
            datasets: dataSet,
        };
        // Create chart using the Chart.js library
        window["religionChart"] = {};
        if (document.getElementById("religionChart")) {
            const ctx = document.getElementById("religionChart").getContext("2d");
            religionChart = new Chart(ctx, {
                type: "doughnut",
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: (e, activeEls) => {
                        let datasetIndex = activeEls[0].datasetIndex;
                        let dataIndex = activeEls[0].index;
                        let datasetLabel = e.chart.data.datasets[datasetIndex].label;
                        let value = e.chart.data.datasets[datasetIndex].data[dataIndex];
                        let label = e.chart.data.labels[dataIndex];
                        localStorage.removeItem("savedFilters");
                        window.location.href =
                            "/employee/employee-view?religion=" + label;
                    },
                },
                plugins: [
                    {
                        afterRender: (chart) => emptyChart(chart),
                    },
                ],
            });
        }
    }

    function bloodGroup(dataSet, labels) {
        const data = {
            labels: labels,
            datasets: dataSet,
        };
        // Create chart using the Chart.js library
        window["bloodGroup"] = {};
        if (document.getElementById("bloodGroup")) {
            const ctx = document.getElementById("bloodGroup").getContext("2d");
            bloodGroup = new Chart(ctx, {
                type: "doughnut",
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: (e, activeEls) => {
                        let datasetIndex = activeEls[0].datasetIndex;
                        let dataIndex = activeEls[0].index;
                        let datasetLabel = e.chart.data.datasets[datasetIndex].label;
                        let value = e.chart.data.datasets[datasetIndex].data[dataIndex];
                        let label = e.chart.data.labels[dataIndex];
                        localStorage.removeItem("savedFilters");
                        window.location.href =
                            "/employee/employee-view?bloodGroup=" + label;
                    },
                },
                plugins: [
                    {
                        afterRender: (chart) => emptyChart(chart),
                    },
                ],
            });
        }
    }

    function maritalChart(dataSet, labels) {
        const data = {
            labels: labels,
            datasets: dataSet,
        };
        // Create chart using the Chart.js library
        window["maritalChart"] = {};
        if (document.getElementById("maritalChart")) {
            const ctx = document.getElementById("maritalChart").getContext("2d");
            maritalChart = new Chart(ctx, {
                type: "doughnut",
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: (e, activeEls) => {
                        let datasetIndex = activeEls[0].datasetIndex;
                        let dataIndex = activeEls[0].index;
                        let datasetLabel = e.chart.data.datasets[datasetIndex].label;
                        let value = e.chart.data.datasets[datasetIndex].data[dataIndex];
                        let label = e.chart.data.labels[dataIndex];
                        localStorage.removeItem("savedFilters");
                        window.location.href =
                            "/employee/employee-view?marital_status=" + label;
                    },
                },
                plugins: [
                    {
                        afterRender: (chart) => emptyChart(chart),
                    },
                ],
            });
        }
    }

    function departmentChart(dataSet, labels) {
        const data = {
            labels: labels,
            datasets: dataSet,
        };
        // Create chart using the Chart.js library
        window["departmentChart"] = {};
        if (document.getElementById("departmentChart")) {
            const ctx = document.getElementById("departmentChart").getContext("2d");
            departmentChart = new Chart(ctx, {
                type: "doughnut",
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: (e, activeEls) => {
                        let datasetIndex = activeEls[0].datasetIndex;
                        let dataIndex = activeEls[0].index;
                        let datasetLabel = e.chart.data.datasets[datasetIndex].label;
                        let value = e.chart.data.datasets[datasetIndex].data[dataIndex];
                        let label = e.chart.data.labels[dataIndex];
                        localStorage.removeItem("savedFilters");
                        window.location.href =
                            "/employee/employee-view?department=" + label;

                    },
                },
                plugins: [
                    {
                        afterRender: (chart) => emptyChart(chart),
                    },
                ],
            });
        }
    }

    function gradeChart(dataSet, labels) {
        const data = {
            labels: labels,
            datasets: dataSet,
        };
        // Create chart using the Chart.js library
        window["gradeChart"] = {};
        if (document.getElementById("gradeChart")) {
            const ctx = document.getElementById("gradeChart").getContext("2d");
            gradeChart = new Chart(ctx, {
                type: "doughnut",
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: (e, activeEls) => {
                        let datasetIndex = activeEls[0].datasetIndex;
                        let dataIndex = activeEls[0].index;
                        let datasetLabel = e.chart.data.datasets[datasetIndex].label;
                        let value = e.chart.data.datasets[datasetIndex].data[dataIndex];
                        let label = e.chart.data.labels[dataIndex];
                        localStorage.removeItem("savedFilters");
                        window.location.href =
                            "/employee/employee-view?grade=" + label;

                    },
                },
                plugins: [
                    {
                        afterRender: (chart) => emptyChart(chart),
                    },
                ],
            });
        }
    }

    function unitChart(dataSet, labels) {
        const data = {
            labels: labels,
            datasets: dataSet,
        };
        // Create chart using the Chart.js library
        window["unitChart"] = {};
        if (document.getElementById("unitChart")) {
            const ctx = document.getElementById("unitChart").getContext("2d");
            unitChart = new Chart(ctx, {
                type: "doughnut",
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: (e, activeEls) => {
                        let datasetIndex = activeEls[0].datasetIndex;
                        let dataIndex = activeEls[0].index;
                        let datasetLabel = e.chart.data.datasets[datasetIndex].label;
                        let value = e.chart.data.datasets[datasetIndex].data[dataIndex];
                        let label = e.chart.data.labels[dataIndex];
                        localStorage.removeItem("savedFilters");
                        window.location.href =
                            "/employee/employee-view?unit=" + label;

                    },
                },
                plugins: [
                    {
                        afterRender: (chart) => emptyChart(chart),
                    },
                ],
            });
        }
    }

    function sectionChart(dataSet, labels) {
        const data = {
            labels: labels,
            datasets: dataSet,
        };
        // Create chart using the Chart.js library
        window["sectionChart"] = {};
        if (document.getElementById("sectionChart")) {
            const ctx = document.getElementById("sectionChart").getContext("2d");
            sectionChart = new Chart(ctx, {
                type: "doughnut",
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: (e, activeEls) => {
                        let datasetIndex = activeEls[0].datasetIndex;
                        let dataIndex = activeEls[0].index;
                        let datasetLabel = e.chart.data.datasets[datasetIndex].label;
                        let value = e.chart.data.datasets[datasetIndex].data[dataIndex];
                        let label = e.chart.data.labels[dataIndex];
                        localStorage.removeItem("savedFilters");
                        window.location.href =
                            "/employee/employee-view?section=" + label;

                    },
                },
                plugins: [
                    {
                        afterRender: (chart) => emptyChart(chart),
                    },
                ],
            });
        }
    }

    function positionsChart(dataSet, labels) {
        const data = {
            labels: labels,
            datasets: dataSet,
        };
        // Create chart using the Chart.js library
        window["positionsChart"] = {};
        if (document.getElementById("positionsChart")) {
            const ctx = document.getElementById("positionsChart").getContext("2d");
            positionsChart = new Chart(ctx, {
                type: "doughnut",
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: (e, activeEls) => {
                        let datasetIndex = activeEls[0].datasetIndex;
                        let dataIndex = activeEls[0].index;
                        let datasetLabel = e.chart.data.datasets[datasetIndex].label;
                        let value = e.chart.data.datasets[datasetIndex].data[dataIndex];
                        let label = e.chart.data.labels[dataIndex];
                        localStorage.removeItem("savedFilters");
                        window.location.href =
                            "/employee/employee-view?position=" + label;

                    },
                },
                plugins: [
                    {
                        afterRender: (chart) => emptyChart(chart),
                    },
                ],
            });
        }
    }

    function categoryChart(dataSet, labels) {
        const data = {
            labels: labels,
            datasets: dataSet,
        };
        // Create chart using the Chart.js library
        window["categoryChart"] = {};
        if (document.getElementById("categoryChart")) {
            const ctx = document.getElementById("categoryChart").getContext("2d");
            categoryChart = new Chart(ctx, {
                type: "doughnut",
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: (e, activeEls) => {
                        let datasetIndex = activeEls[0].datasetIndex;
                        let dataIndex = activeEls[0].index;
                        let datasetLabel = e.chart.data.datasets[datasetIndex].label;
                        let value = e.chart.data.datasets[datasetIndex].data[dataIndex];
                        let label = e.chart.data.labels[dataIndex];
                        localStorage.removeItem("savedFilters");
                        window.location.href =
                            "/employee/employee-view?category=" + label;

                    },
                },
                plugins: [
                    {
                        afterRender: (chart) => emptyChart(chart),
                    },
                ],
            });
        }
    }


    $.ajax({
        url: "/employee/dashboard-employee",
        type: "GET",
        success: function (response) {
          // Code to handle the response
          dataSet = response.dataSet;
          labels = response.labels;

          employeeChart(dataSet, labels);
        },
    });

    $.ajax({
        url: "/employee/dashboard-employee-gender",
        type: "GET",
        success: function (response) {
            // Code to handle the response
            dataSet = response.dataSet;
            labels = response.labels;
            genderChart(dataSet, labels);
        },
    });

    $.ajax({
        url: "/employee/dashboard-employee-relegion",
        type: "GET",
        success: function (response) {
            // Code to handle the response
            dataSet = response.dataSet;
            labels = response.labels;
            religionChart(dataSet, labels);
        },
    });

     $.ajax({
        url: "/employee/dashboard-employee-blood-group",
        type: "GET",
        success: function (response) {
            // Code to handle the response
            dataSet = response.dataSet;
            labels = response.labels;
            bloodGroup(dataSet, labels);
        },
    });

     $.ajax({
        url: "/employee/dashboard-employee-marital-status",
        type: "GET",
        success: function (response) {
            // Code to handle the response
            dataSet = response.dataSet;
            labels = response.labels;
            maritalChart(dataSet, labels);
        },
    });

    $.ajax({
        url: "/employee/dashboard-employee-department",
        type: "GET",
        success: function (response) {
            // Code to handle the response
            dataSet = response.dataSet;
            labels = response.labels;
            departmentChart(dataSet, labels);
        },
        error: function (error) {
            console.log(error);
        },
    });

    $.ajax({
        url: "/employee/dashboard-employee-job-position",
        type: "GET",
        success: function (response) {
            // Code to handle the response
            dataSet = response.dataSet;
            labels = response.labels;
            positionsChart(dataSet, labels);
        },
        error: function (error) {
            console.log(error);
        },
    });

    $.ajax({
        url: "/employee/dashboard-employee-job-section",
        type: "GET",
        success: function (response) {
            // Code to handle the response
            dataSet = response.dataSet;
            labels = response.labels;
            sectionChart(dataSet, labels);
        },
        error: function (error) {
            console.log(error);
        },
    });

    $.ajax({
        url: "/employee/dashboard-employee-job-unit",
        type: "GET",
        success: function (response) {
            // Code to handle the response
            dataSet = response.dataSet;
            labels = response.labels;
            unitChart(dataSet, labels);
        },
        error: function (error) {
            console.log(error);
        },
    });

    $.ajax({
        url: "/employee/dashboard-employee-job-grade",
        type: "GET",
        success: function (response) {
            // Code to handle the response
            dataSet = response.dataSet;
            labels = response.labels;
            gradeChart(dataSet, labels);
        },
        error: function (error) {
            console.log(error);
        },
    });

    $.ajax({
        url: "/employee/dashboard-employee-category",
        type: "GET",
        success: function (response) {
            // Code to handle the response
            dataSet = response.dataSet;
            labels = response.labels;
            console.log(dataSet,'category')
            categoryChart(dataSet, labels);
        },
        error: function (error) {
            console.log(error);
        },
    });

    $(".oh-card-dashboard__title").click(function (e) {
        var chartType = myChart.config.type;
        if (chartType === "line") {
            chartType = "bar";
        } else if (chartType === "bar") {
            chartType = "doughnut";
        } else if (chartType === "doughnut") {
            chartType = "pie";
        } else if (chartType === "pie") {
            chartType = "line";
        }
        myChart.config.type = chartType;
        myChart.update();
    });
});
