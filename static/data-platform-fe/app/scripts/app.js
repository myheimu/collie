'use strict'
angular.module('dataPlatformApp', [
  'ngRoute',
  'ngSanitize',
  'ui.bootstrap',
  'ui.codemirror'
])
.config(function($routeProvider, $httpProvider) {
  $httpProvider.interceptors.push('authInterceptor')
  $routeProvider
    .when('/', {
      templateUrl: 'views/recent.html',
      controller: 'Recent'
    })
    .when('/create-table', {
      templateUrl: 'views/create-table.html',
      controller: 'CreateTable'
    })
    .when('/register-table', {
      templateUrl: 'views/register-table.html',
      controller: 'RegisterTable'
    })
    .when('/log-table/:id', {
      templateUrl:'views/register-table.html',
      controller: 'RegisterTable'
    })
    .when('/create-table-success/:id', {
      templateUrl: 'views/create-table-success.html',
      controller: 'CreateTableSuccess'
    })
    .when('/table/:id', {
      templateUrl:'views/table.html',
      controller: 'Table'
    })
    .when('/create-task', {
      templateUrl: 'views/create-task.html',
      controller: 'CreateTask'
    })
    .otherwise({
      redirectTo: '/'
    })
})

.config(function($provide) {
  // 为$http增加一个传统的表单post方法,名曰$post
  $provide.decorator('$http', ['$delegate',function($delegate){
    $delegate.$post = function(url,data){
      return $delegate.post(url,$.param(data),{
        headers:{
          'Content-Type':'application/x-www-form-urlencoded'
        }
      })
    }
    return $delegate// 最后一定要return
  }])
})

.controller('Sidebar', function($scope, Table){
  Table.getLogTableTree().success(function(result){
    $scope.productLine = result.data
  })
})

.controller('User', function($scope, User){
  User.info().success(function(data){
    $scope.user_info = data.user_info
  })
})

.controller('Recent', function($scope, Table, $routeParams){
  $scope.isActive = function(tab){
    if(tab == $routeParams.tab){
      return true
    }
    return false
  }

  Table.latest().success(function(data){
    $scope.recentTables = data.tables
  })

  Table.getLogTableList().success(function(data){
    $scope.logTables = data.table_info_list
  })
})

.controller('Table', function($scope, $routeParams, Table){
  Table.get($routeParams.id).success(function(data){
    $scope.table = data.table_info
  })
})

.controller('CreateTable', function($scope, $routeParams, Table, $location, Common){
  $scope.fieldTypes = Common.fieldTypes
  $scope.table = {
    columns:[{}],
    service_id:1
  }

  // 如果有id,说明是编辑表
  if($routeParams.id){
    Table.get(id).success(function(data){
      $scope.table = data
    })
  }

  // 提交
  $scope.createTable = function(){
    Table.create($scope.table).success(function(data){
      $location.path('/create-table-success/'+data.table_id)
    })
  }
})

.controller('RegisterTable', function($scope, $routeParams, Table, $location, Common, editorOptions){
  $scope.table = {}
  $scope.editorOptions = editorOptions
  $scope.fieldTypes = Common.fieldTypes

  $scope.file_format_option = {
    "log-data":["Sequence-File"],
    "temp-data":["parquet", "textfile", "Sequence-File"]
  }
  $scope.deser_format_tips = {
    "delimited":'"delimited"="\\t","key"="value"',
    "thrift":'serialization.class="",\nserialization.format=""'
  }

  var tableBak
  $scope.edit = function(){// 编辑
    editingWatch();
    $scope.editing = true
    tableBak = angular.copy($scope.table)// 备份一份,用于取消时恢复
  }
  $scope.cancel = function(){// 取消编辑
    editingUnWatch();
    $scope.editing = false
    $scope.table = tableBak
  }

  var data_type_watch
  var name_watch
  var editingWatch = function(){
    data_type_watch = $scope.$watch(function(){
      return {
        data_type:$scope.table.data_type,
        editing:$scope.editing
      }
    },function(newVal,oldVal){
      if(oldVal.editing == false || angular.equals(newVal,oldVal)){
        return;//从非编辑状态切到编辑状态是不需要联动效果的
      }
      if(newVal.data_type == 'log-data'){//日志
        $scope.table.file_type = 'Sequence-File'
        $scope.table.deser_format = 'delimited'
        $scope.table.serde_params = ''
        $scope.table.is_partition = true
      }
      if(newVal.data_type == 'temp-data'){//中间数据
        $scope.table.file_type = 'parquet'
        $scope.table.is_partition = false
      }
    },true)

    name_watch = $scope.$watch('table.name + table.data_type',function(){
      if($scope.table.data_type == 'log-data'){
        $scope.table.uri = '/user/h_scribe/' + ($scope.table.name || '')
      }
      if($scope.table.data_type == 'temp-data'){
        $scope.table.uri = '/xx/oo/' + ($scope.table.name || '')
      }
    })
  }
  var editingUnWatch = function(){
    data_type_watch()
    name_watch()
  }

  if($routeParams.id){
    $scope.editing = false
    $scope.viewTable = true // 查看已有表的界面
    Table.getLogTable($routeParams.id).success(function(data){
      $scope.table = data.table_info
    })
  }else{
    editingWatch()
  }

  // 提交
  $scope.submit = function(){
    Table.register($scope.table).success(function(data){

      if(data.error_msg){
        alert(data.error_msg)
        return
      }

      $scope.editing = false// 提交完成后将编辑状态置为非
      editingUnWatch()
      $location.path('/log-table/' + data.table_info.id)
    })
  }
})

.controller('CreateTableSuccess', function($scope, $routeParams){
  $scope.tableId = $routeParams.id
})

.controller('CreateTask', function($scope){
  $scope.inputTables = [{}]
})

.filter('emailName',function(){
  return function(email){
    return email.split('@')[0]
  }
})

.constant('Common', {
  fieldTypes: ['bool', 'byte', 'i16', 'i32', 'i64', 'double', 'string', 'binary', 'slist'],
  // BASE: 'http://admin.d.pt.xiaomi.com/data',
  // BASE: 'http://collie.pt.xiaomi.com',
  BASE: 'http://10.237.33.141',
  // BASE: 'http://staging.collie.pt.xiaomi.com',
})

.factory('User', function($http, Common){
  return {
    info: function(){
      return $http.get(Common.BASE + '/profile/nickname')
    }
  }
})

.factory('Table', function($http, Common){
  return {
    latest: function(){
      return $http.get(Common.BASE + '/table/list/latest')
    },
    get: function(id){
      return $http.get(Common.BASE + '/table/describe?table_id=' + id)
    },
    create: function(data){
      return $http.$post(Common.BASE + '/table/create', {
        table_info: JSON.stringify(data)
      })
    },
    register: function(data){
      return $http.$post(Common.BASE + '/table/register', {
        table_info: JSON.stringify(data)
      })
    },
    getLogTable: function(id){
      return $http.get(Common.BASE + '/table/log_table_info?table_id=' + id)
    },
    getLogTableList: function(){
      return $http.get(Common.BASE + '/table/log_table_list')
    },
    getLogTableTree: function(){
      return $http.get(Common.BASE + '/table/log_table_tree')
    }
  }
})

.factory('Task', function($http){
  return {

  }
})

.factory('authInterceptor', function($q){
  return {
    response:function(response){
      if(/内网统一认证系统/.test(response.data) && !/成功/.test(response.data)){
        location.href = 'http://cas.mioffice.cn';
        return $q.reject()
      }
      return response
    }
  }
})

.constant('editorOptions', {
  //lineWrapping: true,
  lineNumbers: true,
  indentWithTabs: true,
  indentUnit: 4,
  matchBrackets: true,
  theme:'midnight',
  mode: 'text/x-c++src'
})
