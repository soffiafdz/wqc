(function() {
  var app=angular.module('qc_app2', [])
  
  app.controller('QCImgController', function($scope, $http) {
    this.current_img=0;
    
    $http.get('get_list')
       .success(function(data, status, headers, config) {
         $scope.qc_files = data;
       })
       
       .error(function(data, status, headers, config) {
         // deal with error!
      });
  });
})();
