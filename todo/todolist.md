#### 完成APISIX Docker的实践与总结

```
// 按奇偶排序数组
    public int[] sortArrayByParity(int[] nums) {
        int n = nums.length;
        if (n < 2) {
            return nums;
        }
        int i = 0, j = n - 1, tmp;
        while (i < j) {
            if (nums[i] % 2 != 0 && nums[j] % 2 == 0) {
                tmp = nums[i];
                nums[i] = nums[j];
                nums[j] = tmp;
            }
            while (nums[i] % 2 == 0) {
                i++;
            }
            while (nums[j] % 2 != 0) {
                j--;
            }
        }
        return nums;
    }
```

```
// 按奇偶排序数组II
    public int[] sortArrayByParityII(int[] nums) {
        int n = nums.length;
        if (n < 2) {
            return nums;
        }
        // 遍历偶数索引，若偶数所指向的元素值为奇数，则将当前奇数索引上的偶数元素值替换
        int i = 0, j = 1, tmp;
        while (i < n) {
            if (nums[i] % 2 != 0) {
                while (nums[j] % 2 != 0) {
                    j += 2;
                }
                tmp = nums[i];
                nums[i] = nums[j];
                nums[j] = tmp;
            }
            i += 2;
        }
        return nums;
    }
```