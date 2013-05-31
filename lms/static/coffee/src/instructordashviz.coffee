@InstructorDashViz = {}

class @InstructorDashViz.GradeDistribution
  constructor: ->
    console.log('hello from InstructorDashViz.GradeDistribution')

  plot: (placeholder, data) ->
    console.log('plotting InstructorDashViz.GradeDistribution')
    window.data = data
    $.plot placeholder, [
      data: data
      bars: {show: true}
    ]

  # plot: (placeholder, data) ->
  #   # TODO invented grade buckets
  #   grade_cutoffs = [['A', 0.90], ['B', 0.80], ['C', 0.50], ['F', 0.0]]

  #   # e.g. ['A', 'A', 'B', 'A']
  #   letter_collection = _.map data, (data) ->
  #     if data.grade >= grade_cutoffs['A']
  #       return 'A'
  #     if data.grade >= grade_cutoffs['B']
  #       return 'B'
  #     if data.grade >= grade_cutoffs['C']
  #       return 'C'
  #     return 'F'

  #   # # e.g {A: 10, B: 20, C: 4, F: 6}
  #   # grade_buckets = _.map , (letter) ->
  #   #   _.filter(letter_collection, (student_letter) -> student_letter == letter).length

  #   # e.g. [['A', 34], ['B', 60], ['C', 15], ['F', 6]]
  #   grade_buckets = _.map grade_cutoffs, ([letter, cutoff]) ->
  #     students_with_letter = _.filter letter_collection, (student_letter) -> student_letter == letter
  #     [letter, students_with_letter.length]

  #   $.plot placeholder, [{data: grade_buckets, bars: {show: true}}]
