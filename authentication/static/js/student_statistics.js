document.addEventListener("DOMContentLoaded", function () {
    /*statistics*/   
    // Get the chart container element
    const BarChart = document.getElementById('Chart');

    // Get the chart type buttons
    const barChartBtn = document.querySelector('.BarChart');
    const lineChartBtn = document.querySelector('.LineChart');
    const pieChartBtn = document.querySelector('.PieChart');
    
    // Define the chart data
    const chartData = {
    labels: ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'],
    datasets: [{
        label: 'Attendance',
        data: [12, 19, 28, 25, 12, 23, 19, 13, 25, 22, 13, 19],
        backgroundColor: [
        'rgba(255, 99, 132, 0.2)', // JAN
        'rgba(54, 162, 235, 0.2)', // FEB
        'rgba(255, 206, 86, 0.2)', // MAR
        'rgba(75, 192, 192, 0.2)', // APR
        'rgba(153, 102, 255, 0.2)', // MAY
        'rgba(255, 159, 64, 0.2)', // JUN
        'rgba(255, 99, 132, 0.2)', // JUL
        'rgba(54, 162, 235, 0.2)', // AUG
        'rgba(255, 206, 86, 0.2)', // SEP
        'rgba(75, 192, 192, 0.2)', // OCT
        'rgba(153, 102, 255, 0.2)', // NOV
        'rgba(255, 159, 64, 0.2)', // DEC
        ],
        borderColor: [
        'rgba(255, 99, 132, 1)', // JAN
        'rgba(54, 162, 235, 1)', // FEB
        'rgba(255, 206, 86, 1)', // MAR
        'rgba(75, 192, 192, 1)', // APR
        'rgba(153, 102, 255, 1)', // MAY
        'rgba(255, 159, 64, 1)', // JUN
        'rgba(255, 99, 132, 1)', // JUL
        'rgba(54, 162, 235, 1)', // AUG
        'rgba(255, 206, 86, 1)', // SEP
        'rgba(75, 192, 192, 1)', // OCT
        'rgba(153, 102, 255, 1)', // NOV
        'rgba(255, 159, 64, 1)', // DEC
        ],
        borderWidth: 1,
        borderRadius: 5
    }]
    };
    
    // Function to initialize the chart
    function initializeChart(type = 'bar') {
    if (chart) {
        chart.destroy(); // Destroy the existing chart
    }
    chart = new Chart(BarChart, {
        type: type,
        data: chartData,
        options: {
        scales: {
            y: {
            beginAtZero: true,
            max: 30,
            }
        }
        }
    });
    }
    
    // Initialize the chart for the first time
    let chart;
    initializeChart();
    
    // Add event listeners to the chart type buttons
    barChartBtn.addEventListener('click', () => {
    initializeChart('bar');
    });
    
    lineChartBtn.addEventListener('click', () => {
    initializeChart('line');
    });
    
    pieChartBtn.addEventListener('click', () => {
    initializeChart('doughnut');
    });

    // Define the chart restart function
    function restartChart() {
        // Destroy the existing chart
        if (chart) {
        chart.destroy();
        }
        // Initialize the chart again
        initializeChart();
    }
    
    // Define the media queries for different window sizes
    const mediaQueries = [
        {
        query: '(max-width: 650px)',
        listener: restartChart,
        },
        {
        query: '(max-width: 1050px)',
        listener: restartChart,
        },
        {
        query: '(min-width: 1051px)',
        listener: restartChart,
        },
    ];
    
    // Create media query listeners
    mediaQueries.forEach((query) => {
        const mediaQueryList = window.matchMedia(query.query);
        mediaQueryList.addListener(query.listener);
        // Trigger the listener once for the initial window size
        query.listener();
    });

        
    /*calender*/
    // Get the calendar container elements
    const calendarContainer = document.querySelector('.calendar-container');
    const calendarContainerNew = document.querySelector('.wrapper-new');
    const dropdownIconN = document.querySelector('#dropdown-icon-N');

    calendarContainer.addEventListener('click', () => {
        dropdownIconN.classList.toggle('rotated');
    });
    
    // Add event listener to the document to close the calendar container new when clicked outside
    document.addEventListener("click", function(event) {
        if (!calendarContainerNew.contains(event.target) && !calendarContainer.contains(event.target)) {
            // Fade out calendarContainerNew
            fadeOut(calendarContainerNew);
            // Reset the dropdown icon to its original state
            dropdownIconN.classList.remove('rotated');
        }
    });

    // Function to toggle the calendar container new
    function toggleCalendarContainerNew() {
        // Only proceed if calendarContainerNew is not already displayed
        if (calendarContainerNew.style.display !== "block") {
            // Fade in calendarContainerNew
            calendarContainerNew.style.display = "block";
            calendarContainerNew.style.opacity = 0;
            fadeIn(calendarContainerNew);
            // Reset to current month when reopened
            currMonthNew = new Date().getMonth();
            currYearNew = new Date().getFullYear();
            monthSelectNew.value = currMonthNew;
            yearSelectNew.value = currYearNew;
            renderCalendarNew();
        } else {
            // Fade out calendarContainerNew
            fadeOut(calendarContainerNew);
        }
    }

    // Add event listener to the calendar container
    calendarContainer.addEventListener("click", toggleCalendarContainerNew);

    // Add event listener to the document to close the calendar container new when clicked outside
    document.addEventListener("click", function(event) {
        if (!calendarContainerNew.contains(event.target) && !calendarContainer.contains(event.target)) {
            // Fade out calendarContainerNew
            fadeOut(calendarContainerNew);
        }
    });

    // Function to fade in an element
    function fadeIn(element) {
        let opacity = 0;
        const interval = setInterval(function () {
            if (opacity < 1) {
                opacity += 0.2;
                element.style.opacity = opacity;
            } else {
                clearInterval(interval);
            }
        }, 50);
    }

    // Function to fade out an element
    function fadeOut(element) {
        let opacity = 1;
        const interval = setInterval(function () {
            if (opacity > 0) {
                opacity -= 0.2;
                element.style.opacity = opacity;
            } else {
                clearInterval(interval);
                element.style.display = "none";
            }
        }, 50);
    }

    /*calender-functionality*/
    const daysTagNew = document.querySelector(".days-new"),
    monthSelectNew = document.getElementById("month-select-new"),
    yearSelectNew = document.getElementById("year-select-new"),
    prevNextIconNew = document.querySelectorAll(".icons-new span");

    // getting new date, current year and month
    let dateNew = new Date(),
    currYearNew = dateNew.getFullYear(),
    currMonthNew = dateNew.getMonth();

    // storing full name of all months in array
    const monthsNew = ["January", "February", "March", "April", "May", "June", "July",
                "August", "September", "October", "November", "December"];

    // Populate month selector
    for (let i = 0; i < monthsNew.length; i++) {
      const option = document.createElement("option");
      option.value = i;
      option.text = monthsNew[i];
      monthSelectNew.appendChild(option);
    }

    // Populate year selector
    let currentYearNew = new Date().getFullYear();
    for (let i = 2000; i <= currentYearNew + 100; i++) {
      const option = document.createElement("option");
      option.value = i;
      option.text = i;
      yearSelectNew.appendChild(option);
    }

    // Set default values
    monthSelectNew.value = currMonthNew;
    yearSelectNew.value = currYearNew;

    const renderCalendarNew = () => {
        let firstDayofMonthNew = new Date(currYearNew, currMonthNew, 1).getDay(), // getting first day of month
        lastDateofMonthNew = new Date(currYearNew, currMonthNew + 1, 0).getDate(), // getting last date of month
        lastDayofMonthNew = new Date(currYearNew, currMonthNew, lastDateofMonthNew).getDay(), // getting last day of month
        lastDateofLastMonthNew = new Date(currYearNew, currMonthNew, 0).getDate(); // getting last date of previous month
        let liTagNew = "";

        for (let i = firstDayofMonthNew; i > 0; i--) { // creating li of previous month last days
            liTagNew += `<li class="inactive">${lastDateofLastMonthNew - i + 1}</li>`;
        }

        for (let i = 1; i <= lastDateofMonthNew; i++) { // creating li of all days of current month
            // adding active class to li if the current day, month, and year matched
            let isTodayNew = i === dateNew.getDate() && currMonthNew === new Date().getMonth() 
                        && currYearNew === new Date().getFullYear() ? "active" : "";
            liTagNew += `<li class="${isTodayNew}">${i}</li>`;
        }

        for (let i = lastDayofMonthNew; i < 6; i++) { // creating li of next month first days
            liTagNew += `<li class="inactive">${i - lastDayofMonthNew + 1}</li>`
        }
        daysTagNew.innerHTML = liTagNew;
    }
    renderCalendarNew();

    // Add event listeners
    monthSelectNew.addEventListener("change", () => {
      currMonthNew = parseInt(monthSelectNew.value);
      renderCalendarNew();
    });

    yearSelectNew.addEventListener("change", () => {
      currYearNew = parseInt(yearSelectNew.value);
      renderCalendarNew();
    });

    prevNextIconNew.forEach(icon => { // getting prev and next icons
        icon.addEventListener("click", () => { // adding click event on both icons
            // if clicked icon is previous icon then decrement current month by 1 else increment it by 1
            if(icon.id === "prev-new") {
                currMonthNew--;
                if(currMonthNew < 0) {
                    currMonthNew = 11;
                    currYearNew--;
                }
            } else {
                currMonthNew++;
                if(currMonthNew > 11) {
                    currMonthNew = 0;
                    currYearNew++;
                }
            }
            monthSelectNew.value = currMonthNew;
            yearSelectNew.value = currYearNew;
            renderCalendarNew(); // calling renderCalendar function
        });
    });

});