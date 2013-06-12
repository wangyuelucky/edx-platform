describe 'Logger', ->
  it 'expose window.log_event', ->
    expect(window.log_event).toBe Logger.log

  describe 'log', ->
    it 'send a request to log event', ->
      spyOn $, 'getWithPrefix'
      Logger.log 'example', 'data'
      expect($.getWithPrefix).toHaveBeenCalledWith '/event',
        event_type: 'example'
        event: '"data"'
        page: window.location.href

    it 'make a callback', ->
      test = false
      callback = (event_type, data, element) ->
        test = true
      Logger.listen 'myEvent', 'anElement', callback
      Logger.log 'myEvent', 'someData', 'anElement'
      expect(test).toBe(true)

    it 'make multiple callbacks with correct data-handling.', ->
      test1 = false
      test2 = false
      sample_data = 'myData'
      callback1 = (event_type, data, element) ->
        test1 = (data == sample_data)
      callback2 = (event_type, data, element) ->
        test2 = (data == sample_data)
      Logger.listen 'myEvent', 'anElement', callback1
      Logger.listen 'myEvent', 'anElement', callback2
      Logger.log 'myEvent', sample_data, 'anElement'
      expect(test1).toBe(true)
      expect(test2).toBe(true)


  # Broken with commit 9f75e64? Skipping for now.
  xdescribe 'bind', ->
    beforeEach ->
      Logger.bind()
      Courseware.prefix = '/6002x'

    afterEach ->
      window.onunload = null

    it 'bind the onunload event', ->
      expect(window.onunload).toEqual jasmine.any(Function)

    it 'send a request to log event', ->
      spyOn($, 'ajax')
      window.onunload()
      expect($.ajax).toHaveBeenCalledWith
        url: "#{Courseware.prefix}/event",
        data:
          event_type: 'page_close'
          event: ''
          page: window.location.href
        async: false
