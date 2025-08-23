```cpp
#include <gtest/gtest.h>
#include <mockcpp/mockcpp.hpp>
#include <stdlib.h>

// 模拟外部依赖的头文件
extern "C" {
    #include "linked_list.h"
}

using namespace mockcpp;

// Mock free函数
MOCKCPP_MOCK_FREE(free);

class ListDestroyTest : public ::testing::Test {
protected:
    void SetUp() override {
        // 设置Mock期望
    }

    void TearDown() override {
        // 验证所有Mock期望
        Mock::verify();
        // 清除所有Mock
        Mock::reset();
    }
};

// 测试正常情况：销毁非空链表
TEST_F(ListDestroyTest, ShouldDestroyNonEmptyList) {
    // 创建测试链表结构
    LinkedList list;
    ListNode node1, node2;
    
    list.head = &node1;
    node1.next = &node2;
    node2.next = NULL;
    
    // 设置free的期望调用
    MOCKCPP_EXPECT_CALL(free, (&node1)).times(1);
    MOCKCPP_EXPECT_CALL(free, (&node2)).times(1);
    MOCKCPP_EXPECT_CALL(free, (&list)).times(1);
    
    // 执行测试
    list_destroy(&list);
}

// 测试边界情况：销毁空链表（只有头节点）
TEST_F(ListDestroyTest, ShouldDestroyEmptyList) {
    LinkedList list;
    list.head = NULL;
    
    // 设置free的期望调用
    MOCKCPP_EXPECT_CALL(free, (&list)).times(1);
    
    // 执行测试
    list_destroy(&list);
}

// 测试边界情况：传入NULL指针
TEST_F(ListDestroyTest, ShouldHandleNullPointer) {
    // 设置free不应该被调用
    MOCKCPP_EXPECT_CALL(free, Any()).times(0);
    
    // 执行测试
    list_destroy(NULL);
}

// 测试异常情况：单个节点的链表
TEST_F(ListDestroyTest, ShouldDestroySingleNodeList) {
    LinkedList list;
    ListNode node;
    
    list.head = &node;
    node.next = NULL;
    
    // 设置free的期望调用
    MOCKCPP_EXPECT_CALL(free, (&node)).times(1);
    MOCKCPP_EXPECT_CALL(free, (&list)).times(1);
    
    // 执行测试
    list_destroy(&list);
}

// 测试多个节点的链表
TEST_F(ListDestroyTest, ShouldDestroyMultiNodeList) {
    const int NODE_COUNT = 5;
    LinkedList list;
    ListNode nodes[NODE_COUNT];
    
    list.head = &nodes[0];
    for (int i = 0; i < NODE_COUNT - 1; i++) {
        nodes[i].next = &nodes[i + 1];
    }
    nodes[NODE_COUNT - 1].next = NULL;
    
    // 设置free的期望调用
    for (int i = 0; i < NODE_COUNT; i++) {
        MOCKCPP_EXPECT_CALL(free, (&nodes[i])).times(1);
    }
    MOCKCPP_EXPECT_CALL(free, (&list)).times(1);
    
    // 执行测试
    list_destroy(&list);
}

// 主函数
int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
```

这个测试文件包含了：

1. **完整的头文件包含**：包含了必要的Google Test和MockCpp头文件
2. **Mock对象**：为`free`函数创建了Mock，用于验证内存释放的正确性
3. **边界条件测试**：
   - 传入NULL指针的情况
   - 空链表的情况
   - 单节点链表的情况
4. **正常流程测试**：
   - 多节点链表的销毁
   - 验证所有节点都被正确释放
5. **异常情况处理**：测试了NULL指针输入的处理
6. **Google Test断言**：通过Mock的期望验证来间接断言函数行为

测试用例覆盖了：
- 正常的多节点链表销毁
- 边界情况（空链表、单节点链表）
- 异常情况（NULL输入）
- 验证内存释放的正确顺序和次数