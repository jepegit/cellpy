// Show "Was this page helpful?" without Google Analytics.
// The theme renders the form hidden; the stock unhide lives in the
// Google provider script, which this site does not load.
if (typeof document$ !== "undefined") {
  document$.subscribe(function () {
    var form = document.forms.feedback;
    if (!form || form.dataset.cellpyFeedback === "1") {
      return;
    }
    form.dataset.cellpyFeedback = "1";
    form.hidden = false;
    var buttons = form.querySelectorAll("[type=submit]");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].addEventListener("click", function (event) {
        event.preventDefault();
        var value = this.getAttribute("data-md-value");
        var fieldset = form.querySelector("fieldset");
        if (fieldset) {
          fieldset.disabled = true;
        }
        var note = form.querySelector(
          ".md-feedback__note [data-md-value='" + value + "']"
        );
        if (note) {
          note.hidden = false;
        }
      });
    }
  });
}
