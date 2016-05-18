(function() { 
  var app=angular.module('qc_app', [])
  
  app.controller('QCListController', function($scope, $http) {
    $http.get('get_list')
      .success(function(data, status, headers, config) {
        this.qc_files = data;
      })
      .error(function(data, status, headers, config) {
        //TODO: handle error?
      });
  });
})();
