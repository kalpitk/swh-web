import {createVisitsHistogram} from './visits-histogram';
import {updateCalendar} from './visits-calendar';
import './visits-reporting.css';

// will hold all visits
let allVisits;
// will hold filtered visits to display
let filteredVisits;
// will hold currently displayed year
let currentYear;

// function to gather full visits
function filterFullVisits(differentSnapshots) {
  let filteredVisits = [];
  for (let i = 0; i < allVisits.length; ++i) {
    if (allVisits[i].status !== 'full') continue;
    if (!differentSnapshots) {
      filteredVisits.push(allVisits[i]);
    } else if (filteredVisits.length === 0) {
      filteredVisits.push(allVisits[i]);
    } else {
      let lastVisit = filteredVisits[filteredVisits.length - 1];
      if (allVisits[i].snapshot !== lastVisit.snapshot) {
        filteredVisits.push(allVisits[i]);
      }
    }
  }
  return filteredVisits;
}

// function to update the visits list view based on the selected year
function updateVisitsList(year) {
  $('#swh-visits-list').children().remove();
  let visitsByYear = [];
  for (let i = 0; i < filteredVisits.length; ++i) {
    if (filteredVisits[i].date.getUTCFullYear() === year) {
      visitsByYear.push(filteredVisits[i]);
    }
  }
  let visitsCpt = 0;
  let nbVisitsByRow = 4;
  let visitsListHtml = '<div class="swh-visits-list-row">';
  for (let i = 0; i < visitsByYear.length; ++i) {
    if (visitsCpt > 0 && visitsCpt % nbVisitsByRow === 0) {
      visitsListHtml += '</div><div class="swh-visits-list-row">';
    }
    visitsListHtml += '<div class="swh-visits-list-column" style="width: ' + 100 / nbVisitsByRow + '%;">';
    visitsListHtml += '<a class="swh-visit-' + visitsByYear[i].status + '" title="' + visitsByYear[i].status +
                        ' visit" href="' + visitsByYear[i].browse_url + '">' + visitsByYear[i].fmt_date + '</a>';
    visitsListHtml += '</div>';
    ++visitsCpt;
  }
  visitsListHtml += '</div>';
  $('#swh-visits-list').append($(visitsListHtml));
}

// callback when the user selects a year through the visits histogram
function yearClicked(year) {
  currentYear = year;
  updateCalendar(year, filteredVisits);
  updateVisitsList(year);
}

// function to update the visits views (histogram, calendar, list)
function updateDisplayedVisits() {
  if (filteredVisits.length === 0) {
    return;
  }
  if (!currentYear) {
    currentYear = filteredVisits[filteredVisits.length - 1].date.getUTCFullYear();
  }
  createVisitsHistogram('.d3-wrapper', filteredVisits, currentYear, yearClicked);
  updateCalendar(currentYear, filteredVisits);
  updateVisitsList(currentYear);
}

// callback when the user only wants to see full visits pointing
// to different snapshots (default)
export function showFullVisitsDifferentSnapshots(event) {
  if (event) {
    $('.swh-visits-button').removeClass('active');
    $(event.currentTarget).addClass('active');
  }
  filteredVisits = filterFullVisits(true);
  updateDisplayedVisits();
}

// callback when the user only wants to see full visits
export function showFullVisits(event) {
  if (event) {
    $('.swh-visits-button').removeClass('active');
    $(event.currentTarget).addClass('active');
  }
  filteredVisits = filterFullVisits(false);
  updateDisplayedVisits();
}

// callback when the user wants to see all visits (including partial, ongoing and failed ones)
export function showAllVisits(event) {
  if (event) {
    $('.swh-visits-button').removeClass('active');
    $(event.currentTarget).addClass('active');
  }
  filteredVisits = allVisits;
  updateDisplayedVisits();
}

export function initVisitsReporting(visits) {

  allVisits = visits;
  // process input visits
  let firstFullVisit;
  allVisits.forEach((v, i) => {
    // Turn Unix epoch into Javascript Date object
    v.date = new Date(Math.floor(v.date * 1000));
    let visitLink = '<a class="swh-visit-' + v.status + '" href="' + v.browse_url + '">' + v.fmt_date + '</a>';
    if (v.status === 'full') {
      if (!firstFullVisit) {
        firstFullVisit = v;
        $('#swh-first-full-visit').append($(visitLink));
      } else {
        $('#swh-last-full-visit')[0].innerHTML = visitLink;
      }
    }
    if (i === allVisits.length - 1) {
      $('#swh-last-visit').append($(visitLink));
    }
  });

  // display full visits pointing to different snapshots by default
  showFullVisitsDifferentSnapshots();

}