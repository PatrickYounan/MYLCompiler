# About
An assembly compiler written with the Python Language.

# Todo list
- [ ] Local Variables<br>
  - [x] Int: i8, i16, i32, i64 
  - [ ] Float: f64
- [x] Function calls
- [x] Arithmetic (+, -, *, /)
- [ ] Global data storage (variables)
- [ ] Arrays
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
  i64 age = get_age()
  printf("Here %d", age)
end

def get_age() : i64
  i64 result = 64
  return result
end
```

# Compiling
You will need Python installed, NASM and MinGW64 to compile and run the generated exe.

https://www.python.org/
<br>
https://www.nasm.us/
<br>
https://www.mingw-w64.org/
