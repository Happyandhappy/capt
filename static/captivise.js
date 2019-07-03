;var locale = {
  "decimal": ".",
  "thousands": ",",
  "grouping": [3],
  "currency": ["£", ""],
  "dateTime": "%a %b %e %X %Y",
  "date": "%d/%m/%Y",
  "time": "%H:%M:%S",
  "periods": ["AM", "PM"],
  "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
  "shortDays": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
  "months": [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December"
    ],
  "shortMonths": [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
};

function formatDate (momentDate) {
  return momentDate.format('DD/MM/YYYY');
}

var timePeriodGetters = {
  last30Days: function () {
    return {
      from: formatDate(moment().subtract(30, 'days')),
      to: formatDate(moment())
    };
  },
  thisWeek: function () {
    return {
      from: formatDate(moment().subtract(7, 'days')),
      to: formatDate(moment())
    };
  },
  lastWeek: function () {
    return {
      from: formatDate(moment().subtract(14, 'days')),
      to: formatDate(moment().subtract(7, 'days'))
    };
  },
  thisMonth: function () {
    return {
      from: formatDate(moment().subtract(1, 'months')),
      to: formatDate(moment())
    };
  },
  lastMonth: function () {
    return {
      from: formatDate(moment().subtract(2, 'months')),
      to: formatDate(moment().subtract(1, 'months'))
    };
  },
  thisYear: function () {
    return {
      from: formatDate(moment().subtract(1, 'years')),
      to: formatDate(moment())
    };
  },
  lastYear: function () {
    return {
      from: formatDate(moment().subtract(2, 'years')),
      to: formatDate(moment().subtract(1, 'years'))
    };
  },
};

$(function () {

  $('select').uniform();

  $('.accordion').accordion({
    collapsible: true,
    active: false,
    heightStyle: 'content'
  });

  var charts = $('.js-chart');

  if (charts.length > 0) {
    d3locale = d3.locale(locale);

    charts.each(function () {
      var keys = Object.keys(this.metrics);
      keys.sort();
      var rows = [['x', 'CPA', 'Conversions']];

      for (var i=0; i < keys.length; i++) {
        var key = keys[i];
        var item = this.metrics[key];
        rows.push([key, item['cpc'], item['conversions']]);
      }

      var earliest_date = moment(keys[0]);
      var latest_date = moment(keys[keys.length - 1]);
      var overSixMonths = latest_date.diff(earliest_date, 'months') >= 6;

      var chartOptions = {
        bindTo: '#' + this.id,
        data: {
          x: 'x',
          rows: rows,
          axes: {
            Conversions: 'y2'
          }
        },
        axis: {
          x: {
            type: 'timeseries',
            tick: {
              rotate: 75
            }
          },
          y: { tick: { format: d3locale.numberFormat("$,.2f") } },
          y2: { show: true }
        }
      };

      if (overSixMonths) {
        chartOptions.point = { show: false };
        chartOptions.axis.x.tick.culling = { max: 13 };
        chartOptions.axis.x.tick.format = '%Y-%m';
      } else {
        chartOptions.axis.x.tick.culling = false;
        chartOptions.axis.x.tick.format = '%Y-%m-%d';
      }

      this.chart = c3.generate(chartOptions);
    });
  }

  $('.js-date-range').each(function () {
    $(this).find('[id*=date]').datepicker({
      constrainInput: true,
      dateFormat: 'dd/mm/yy',
      maxDate: 0
    });

    $(this).find('.js-date-range-selector').change(function () {
      var form = $(this.form);
      var fromInput = form.find('#id_date_from');
      var toInput = form.find('#id_date_to');

      var selected = $(this).find('option:selected').val();

      var timePeriodGetter = timePeriodGetters[selected];

      if (!!timePeriodGetter) {
        timePeriod = timePeriodGetter();

        fromInput.val(timePeriod.from);
        toInput.val(timePeriod.to);
      }
    });
  });

  $('.js-dismiss-banner-form').each(function () {
    var form = $(this);
    form.find('.js-submit').click(function () {
      $.ajax({
        url: form.attr('action'),
        type: form.attr('method'),
        data: form.serialize()
      });

      var bannerName = form.find('input[name=banner_name]').val();

      $('[data-name=' + bannerName + ']').remove();
    });
  });
});
