@InstructorDashViz = {}

class @InstructorDashViz.GradeDistribution
  constructor: ->
    console.log('hello from InstructorDashViz.GradeDistribution')

  plot: (placeholder, data) ->
    console.log('plotting InstructorDashViz.GradeDistribution')

    $.plot placeholder, [data.data], {
      bars: {show: true}
      xaxis: tickFormatter: (val, axis) -> (data.ascending_grades.concat [''])[val]
    }

class @InstructorDashViz.EnrollmentChange
  constructor: ->
    console.log('hello from InstructorDashViz.EnrollmentChange')

  plot: (placeholder, data) ->
    console.log('plotting InstructorDashViz.EnrollmentChange')

    $.plot placeholder, [data.data], {
      lines: {
        steps: true
      }
    }
