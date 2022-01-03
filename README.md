# About
An assembly compiler written with the Python Language.

# Todo list
- [x] Local Int Variables (i8, i16, i32, i64)
- [x] Function calls
- [x] Arithmetic (+, -, *, /)
- [ ] Global data storage (variables)
- [ ] Condition checking (if, else, else if)
- [ ] Loops (while, for)
- [ ] Structs
- [ ] Enums 
- [ ] Optimized Assembly
- [ ] Self Hosting

# Example Code
```
extern printf

pub def main()
  i64 age = 100 / 2
  i64 result = (age / 2) + 10 + 100 - 4
  printf("%d", result)
end
```

# Compiling
You will need Python installed, NASM and MinGW64 to compile and run the generated exe.

https://www.python.org/
<br>
https://www.nasm.us/
<br>
https://www.mingw-w64.org/
