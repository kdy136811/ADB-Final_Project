$("#ShowTargetSchedulebtn").on("click", function () {
  console.log("Entered Show target schedule script");
  console.log($('#uhaveid').val())
  console.log($('#ProjectList option:selected').val())
  $("#targetObserveDiv").children().remove();
  $.ajax({
    url: '/schedule/schedule_show_target',
    type: "POST",
    data: {
      PID: $('#ProjectList option:selected').val(),
      uhaveid: $('#uhaveid').val(),
      time: $('#time').val(),
      SID: $('#SID').val(),
      update_schedule: $('#update_schedule').val()

    },
    datatype: "json",
    success: function (data) {
      console.log(data);
      var targetObservetime = data["targetObservetime"][0];
      console.log(data["targetObservetime"].length);
      var element = `
      <input type="hidden" value="`+ $('#update_schedule').val() + `">
      <input id="t" type="hidden" value="`+ data["targetObservetime"][0]["hour"][0] + `">
      <table>
       <thead>
           <tr>
            <th>Target Name</th>
            <th>Start time</th>
            <th>End time</th>
            <th></th>
            </tr>
           </thead>
           <tbody>
        `;
      $.each(data["targetObservetime"], function (i, item) {
        var time = "[";
        $.each(item.time_section, function (i, item) {
          if (i == 0)
            time = time + item;
          time = time + "," + item;
        });
        time = time + "]";
        element = element + ` 
              <tr>
                <td>`+ item.name + `</td>
                <td>`+ item.start + `</td>
                <td>`+ item.end + `</td>
                <td><button  type="button" class="addTargetSchedule" name="`+ item.TID + `" value="` + time + `">Add</button></td>
              <tr>
            `;
      });
      element = element + `
                </tbody>
              </table>
            `;
      console.log(element);
      $("#targetObserveDiv").prepend(element);
    }
  });
});

$("#targetObserveDiv").on("click", ".addTargetSchedule", function () {
  $.ajax({
    url: '/schedule/schedule_show_target',
    type: "POST",
    data: {
      button: "add",
      time_section: $(this).attr('value'),
      name: $(this).parent().prev().prev().prev().html(),
      TID: $(this).attr('name'),
      PID: $('#ProjectList option:selected').val(),
      uhaveid: $('#uhaveid').val()
    },
    datatype: "json",
    success: function (data) {
      console.log(data);
      console.log($('#update_schedule').val());
      var update_schedule = JSON.parse($('#update_schedule').val());
      console.log(typeof (update_schedule));
      var time = parseInt($('#t').val())
      //var time = parseInt($(this).parent().parent().parent().prev().val());
      console.log(time);
      var tableEl = `<table><thead>`;
      for(var i = 0; i<24; i++){
        if(time<=24)
          tableEl = tableEl + `<th>` + time +`</th>`
        else
          tableEl = tableEl + `<th>` + (time-24) + `</th>`;

        time+=1;
      }

      tableEl += `</thead><tbody>`
      
      $.each(data['schedule'], function (i, item) {
        var sched = new Array(24);
        tableEl += `<tr>`;
        $.each(item['time_section'], function (j, time) {

          if (update_schedule[j] == -2)
            sched[j] = "morning";
          else if(update_schedule[j] == -1)
            if (time != 0) 
                sched[j] = time;
          else
            sched[j] = "Night"
            tableEl+=`<td>`+sched[j]+`</td>`;


        });
        tableEl+=`</tr>`;

        console.log(sched);



      });
      tableEl+=`</tbody></table>`;
      $("#scheduleResult").children().remove();
      $("#scheduleResult").append(tableEl);
    },
    error: function (error) {
      console.log(error);
    }
  });
});




$("#Showmap").click(function () {
  // this is for pop out a map window
  console.log("Entered Show map script");
  window.open("map.html", "popupWindow", "width=600,height=600,scrollbars=yes");
});
