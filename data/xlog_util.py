

def write_thrift(thrift_content):
    '''
    #### this method handle push thrift content into xiaomi-common-logger ####
    #### thrift_content input sample #####
    namespace java com.xiaomi.common.logger.thrift.misearch

    struct CollieTest {
        1: optional i64 uuid = 0;
        2: optional string time = "";
        3: optional string clientIp = "";
        4: optional string serverIp = "";
        5: optional string serverHost = "";
        6: optional string uuidHash = "";
        7: required i64 userId;
        8: required string apiType;
        9: required string content;
    }
    '''

    # running following commands:
    # > git pull
    # > mvn release:prepare
    # > mvn release:perform
    # > git tag # to get latest version in nexus

    # TODO
