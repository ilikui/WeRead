---
title: "C语言 1000问 "
date: 2026-09-02
tags: ["编程", "C语言", "指针"]
summary: "存储类Q3：const 修饰变量和 const 修饰指针，编译器各保证了什么?"
toc: true
---


C语言 1000问 · 存储类Q3：const 修饰变量和 const 修饰指针，编译器各保证了什么？

▎ 五大学习法：费曼学习法——把「const 的左右读法」讲成人话

const 修饰变量的两种情况

- const int x = 5; 或 int const x = 5;：x 本身只读——代码里写 x = 6 编译报错
- 注意：const 变量在 C 里不是编译期常量（不能做数组大小/位域宽度），也不是真只读（绕过指针还能改，那是 UB）

const 修饰指针的两种情况

- `const int *p`（指针指向 const）：p 指向的值只读——*p = 1 报错；但 p 本身可以改（p = &y 合法）
- `int *const p`（const 指针）：p 本身只读——p = &y 报错；但 *p 可以改（*p = 1 合法）
- 读法口诀：const 在 * 左边 → 指向的内容只读；const 在 * 右边 → 指针本身只读
- 还有 `const int *const p`：两者都只读

编译器各保证了什么

- `const int *p`：保证通过 p 不能改所指对象——防止不小心写坏；但对象本身可以被其他指针改
- `int *const p`：保证 p 永远指向同一个对象——防止指针被改指向
- 注意：const 是编译期约束，不是运行期保护——没有硬件/内存保护，恶意绕过照样改

工程用途

- `const int *p`：读函数参数——`void print(const char *s)`：承诺不修改传入的字符串，调用方放心传
- `int *const p`：寄存器基址`（volatile uint32_t *const REG）`：地址固定、内容可写——嵌入式驱动标配
- const 变量：只读配置、表数据放 ROM

一句话总结：const 在 * 左边管内容、在 * 右边管指针；驱动里寄存器基址用「指针 const + 内容 volatile」，函数参数用 const 承诺不改——全是编译期契约，不是运行期防护。