#include <malloc.h>
#include <limits.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>
#include <stdbool.h>
#include <string.h>
#include <math.h>

#ifdef __GNUC__
#  define UNUSED(x) UNUSED_ ## x __attribute__((__unused__))
#else
#  define UNUSED(x) UNUSED_ ## x
#endif

typedef struct object *f_object;

typedef f_object (*function_type)(void *self, f_object args);

enum OBJECT_TYPE {
    NONE, STRING, NUMBER, LIST, CALLABLE, _VARIADIC, REFERENCE, FILE_OBJECT
};

struct object {
    enum OBJECT_TYPE type;
    union {
        char *string;
        double number;
        f_object *reference;
        struct {
            size_t count;
            f_object *elements;
        } list;
        struct {
            void *self;
            function_type func;
        } callable;
        struct {
            FILE *file_ptr;
            char *name;
        } file;
    };
};


f_object false_object;
f_object true_object;
f_object none_object;

void errorf(const char *message, ...) {
    va_list args;
    va_start(args, message);
    vprintf(message, args);
    va_end(args);
    exit(1);
}

void _check_type(f_object arg, enum OBJECT_TYPE type) {
    if (arg->type != type) {
        errorf("Wrong type (expected %i, got %i)", type, arg->type);
    }
}

void _check_length(f_object arg, size_t length) {
    if (arg->list.count != length) {
        errorf("Wrong length (expected %i, got %i)", length, arg->list.count);
    }
}

void _check_length_range(f_object arg, size_t min_length, size_t max_length) {
    if (arg->list.count < min_length || arg->list.count > max_length) {
        errorf("Wrong length (expected between %i and %i, got %i)", min_length, max_length, arg->list.count);
    }
}

void _check_length_min(f_object arg, size_t min_length) {
    if (arg->list.count < min_length) {
        errorf("Wrong length (expected at least %i, got %i)", min_length, arg->list.count);
    }
}

void *copied(void *data, size_t size) {
    void *out = malloc(size);
    memcpy(out, data, size);
    return out;
}

f_object create(enum OBJECT_TYPE type) {
    f_object out = malloc(sizeof(*out));
    out->type = type;
    return out;
}

f_object create_from(struct object data) {
    f_object out = malloc(sizeof(*out));
    *out = data;
    return out;
}

f_object string(char *string) {
    f_object out = create(STRING);
    out->string = string;
    return out;
}

f_object number(double value) {
    f_object out = create(NUMBER);
    out->number = value;
    return out;
}

f_object callable(void *self, function_type func) {
    f_object out = create(CALLABLE);
    out->callable.self = self;
    out->callable.func = func;
    return out;
}

f_object list(size_t size) {
    f_object out = create(LIST);
    out->list.count = size;
    out->list.elements = calloc(size, sizeof(*out->list.elements));
    return out;
}


f_object reference(f_object value) {
    f_object out = create(REFERENCE);
    out->reference = malloc(sizeof(*out->reference));
    *out->reference = value;
    return out;
}

f_object variadic(f_object arg) {
    _check_type(arg, LIST);
    return create_from((struct object) {_VARIADIC, .list=arg->list});
}

f_object list_v(size_t count, ...) {
    va_list args;
    va_start(args, count);
    size_t size = 0;
    f_object *array = calloc(count, sizeof(*array));
    for (size_t i = 0; i < count; i++) {
        array[i] = va_arg(args, f_object);
        if (array[i]->type == _VARIADIC) {
            size += array[i]->list.count;
        } else {
            size += 1;
        }
    }
    va_end(args);
    f_object out = create_from((struct object) {.type = LIST, .list.count=size,
            .list.elements=malloc(sizeof(*out->list.elements) * size)});
    size_t current = 0;
    for (size_t i = 0; i < count; i++) {
        if (array[i]->type == _VARIADIC) {
            memcpy(out->list.elements + current, array[i]->list.elements,
                   sizeof(*out->list.elements) * array[i]->list.count);
            current += array[i]->list.count;
        } else {
            out->list.elements[i] = array[i];
            current += 1;
        }
    }
    return out;
}

f_object sublist(f_object l, size_t start, size_t end) {
    if (start > end || end > l->list.count)
        abort();
    size_t count = end - start;
    f_object out = create_from((struct object) {
            .type = LIST, .list.count=count,
            .list.elements=calloc(count, sizeof(*out->list.elements))});
    memcpy(out->list.elements, l->list.elements + start, sizeof(*out->list.elements) * count);
    return out;
}

f_object call(f_object func, f_object args) {
    _check_type(func, CALLABLE);
    return func->callable.func(func->callable.self, args);
}

void echo_object(f_object arg) {
    switch (arg->type) {
        case NONE:
            printf("None");
            break;
        case STRING:
            printf("%s", arg->string);
            break;
        case NUMBER:
            printf("%f", arg->number);
            break;
        case LIST:
            printf("[");
            if (arg->list.count > 1) {
                echo_object(arg->list.elements[0]);
                for (size_t i = 1; i < arg->list.count; i++) {
                    printf(" ");
                    echo_object(arg->list.elements[i]);
                }
            }
            printf("]");
            break;
        case CALLABLE:
            printf("<function at %p (with %p)>", arg->callable.func, arg->callable.self);
            break;
        case _VARIADIC:
            errorf("Invalid type for echo_object '_VARIADIC'");
        case REFERENCE:
            printf("<Reference: ");
            echo_object(*arg->reference);
            printf(">");
        case FILE_OBJECT:
            printf("<File '%s'>", arg->file.name);
    }
}

bool truthy(f_object arg) {
    switch (arg->type) {
        case NONE:
            return false;
        case STRING:
            return arg->string[0] != '\x00';
        case NUMBER:
            return arg->number != 0;
        case LIST:
            return arg->list.count != 0;
        case CALLABLE:
            return truthy(arg->callable.func(arg->callable.self, list_v(0)));
        case _VARIADIC:
            errorf("Invalid type for truthy 'Variadic'");
        case REFERENCE:
            return true;
        case FILE_OBJECT:
            return true;
    }
}

int cmp(f_object a, f_object b) {
    if (a->type != b->type) errorf("Can't compare different types");
    switch (a->type) {
        case NONE:
            errorf("Can't order NONE");
            break;
        case STRING:
            return strcmp(a->string, b->string);
        case NUMBER:
            return a->number == b->number ? 0 : (a->number > b->number ? 1 : -1);
        case LIST:
            for (size_t i = 0; i < a->list.count; i++) {
                if (i >= b->list.count)return 1;
                int c;
                c = cmp(a->list.elements[i], b->list.elements[i]);
                if (c != 0)return c;
            }
            if (a->list.count < b->list.count)return -1;
            else return 0;
        case CALLABLE:
            errorf("Can't order CALLABLE");
            break;
        case _VARIADIC:
            errorf("Invalid type for emp 'VARIADIC'");
            break;
        case REFERENCE:
            errorf("Can't order REFERENCE");
            break;
        case FILE_OBJECT:
            errorf("Can't order Files");
            break;
    }
    return -2;
}

bool equal(f_object a, f_object b) {
    if (b->type != a->type) {
        return false;
    }
    switch (a->type) {
        case NONE:
            return true;
        case STRING:
            return strcmp(a->string, b->string) == 0;
        case NUMBER:
            return a->number == b->number;
        case LIST:
            if (a->list.count != b->list.count)
                return false;
            for (size_t j = 0; j < a->list.count; j++) {
                if (!equal(a->list.elements[j], a->list.elements[j])) {
                    return false;
                }
            }
            return true;
        case CALLABLE:
            return a->callable.func == b->callable.func && a->callable.self == b->callable.self;
        case _VARIADIC:
            errorf("Variadic for equal\n");
        case REFERENCE:
            return a->reference == b->reference;
        case FILE_OBJECT:
            return a->file.file_ptr == b->file.file_ptr;
    }
}

//region Operators

f_object _call_semicolon(void *UNUSED(self), f_object args) {
    return args->list.elements[args->list.count - 1];
}

f_object _call_add(void *UNUSED(self), f_object args) {
    double sum = 0;
    for (size_t i = 0; i < args->list.count; ++i) {
        _check_type(args->list.elements[i], NUMBER);
        sum += args->list.elements[i]->number;
    }
    return create_from((struct object) {.type=NUMBER, .number = sum});
}

f_object _call_sub(void *UNUSED(self), f_object args) {
    _check_type(args->list.elements[0], NUMBER);
    double sum = args->list.elements[0]->number;
    for (size_t i = 1; i < args->list.count; ++i) {
        _check_type(args->list.elements[i], NUMBER);
        sum -= args->list.elements[i]->number;
    }
    return create_from((struct object) {.type=NUMBER, .number = sum});
}

f_object _call_mul(void *UNUSED(self), f_object args) {
    double product = 1;
    for (size_t i = 0; i < args->list.count; ++i) {
        _check_type(args->list.elements[i], NUMBER);
        product *= args->list.elements[i]->number;
    }
    return (create_from((struct object) {.type=NUMBER, .number = product}));
}

f_object _call_div(void *UNUSED(self), f_object args) {
    _check_type(args->list.elements[0], NUMBER);
    double quotient = args->list.elements[0]->number;
    for (size_t i = 1; i < args->list.count; ++i) {
        _check_type(args->list.elements[i], NUMBER);
        quotient /= args->list.elements[i]->number;
    }
    return (create_from((struct object) {.type=NUMBER, .number = quotient}));
}

f_object _call_pow(void *UNUSED(self), f_object args) {
    _check_type(args->list.elements[0], NUMBER);
    _check_length(args, 2);
    double power = pow(args->list.elements[0]->number, args->list.elements[1]->number);
    /*
    double power = args->list.elements[args->list.count - 1]->number;
    for (size_t i = args->list.count - 1; i >= 0; --i) {
        _check_type(args->list.elements[i], NUMBER);
        power = pow(args->list.elements[i]->number, power);
    }*/
    return (create_from((struct object) {.type=NUMBER, .number = power}));
}

f_object _call_eq(void *UNUSED(self), f_object args) {
    _check_length_min(args, 2);
    f_object arg = args->list.elements[0];
    for (size_t i = 1; i < args->list.count; i++) {
        f_object current = args->list.elements[i];
        if (!equal(arg, current)) {
            return false_object;
        }
    }
    return true_object;
}

f_object _call_ne(void *UNUSED(self), f_object args) {
    _check_length_min(args, 2);
    f_object arg = args->list.elements[0];
    for (size_t i = 1; i < args->list.count; i++) {
        f_object current = args->list.elements[i];
        if (equal(arg, current)) {
            return false_object;
        }
    }
    return true_object;
}

f_object _call_gt(void *UNUSED(self), f_object args) {
    _check_length_min(args, 2);
    for (size_t i = 0; i < args->list.count - 1; i++) {
        if (cmp(args->list.elements[i], args->list.elements[i + 1]) != 1) {
            return false_object;
        }
    }
    return true_object;
}

f_object _call_ge(void *UNUSED(self), f_object args) {
    _check_length_min(args, 2);
    for (size_t i = 0; i < args->list.count - 1; i++) {
        if (cmp(args->list.elements[i], args->list.elements[i + 1]) == -1) {
            return false_object;
        }
    }
    return true_object;
}

f_object _call_lt(void *UNUSED(self), f_object args) {
    _check_length_min(args, 2);
    for (size_t i = 0; i < args->list.count - 1; i++) {
        if (cmp(args->list.elements[i], args->list.elements[i + 1]) != -1) {
            return false_object;
        }
    }
    return true_object;
}

f_object _call_le(void *UNUSED(self), f_object args) {
    _check_length_min(args, 2);
    for (size_t i = 0; i < args->list.count - 1; i++) {
        if (cmp(args->list.elements[i], args->list.elements[i + 1]) == 1) {
            return false_object;
        }
    }
    return true_object;
}

f_object _call_store(void *UNUSED(self), f_object args) {
    _check_length(args, 2);
    f_object ref = args->list.elements[0];
    f_object tar = args->list.elements[1];
    _check_type(ref, REFERENCE);
    *ref->reference = tar;
    return tar;
}

f_object _call_load(void *UNUSED(self), f_object args) {
    _check_length(args, 1);
    _check_type(args->list.elements[0], REFERENCE);
    return *args->list.elements[0]->reference;
}

struct {
    f_object semicolon;

    f_object add;
    f_object sub;
    f_object mul;
    f_object div;
    f_object pow;

    f_object eq;
    f_object ne;
    f_object gt;
    f_object ge;
    f_object le;
    f_object lt;

    f_object store;
    f_object load;
} operators;

//endregion

//region Builtins

f_object _call_print(void *UNUSED(self), f_object args) {
    for (size_t i = 0; i < args->list.count; i++) {
        echo_object(args->list.elements[i]);
        printf(" ");
    }
    printf("\n");
    fflush(stdout);
    return none_object;
}

f_object _call_either(void *UNUSED(self), f_object args) {
    if (args->list.count != 3) {
        errorf("Wrong amount of arguments for either");
    }
    if (truthy(args->list.elements[0])) {
        return args->list.elements[1];
    } else {
        return args->list.elements[2];
    }
}

f_object _call_do(void *UNUSED(self), f_object args) {
    return call(args->list.elements[0], sublist(args, 1, args->list.count));
}

f_object _call_any(void *UNUSED(self), f_object args) {
    for (size_t i = 0; i < args->list.count; i++) {
        if (truthy(args->list.elements[i])) {
            return args->list.elements[i];
        }
    }
    return args->list.elements[args->list.count - 1];
}

f_object _call_all(void *UNUSED(self), f_object args) {
    for (size_t i = 0; i < args->list.count; i++) {
        if (!truthy(args->list.elements[i])) {
            return args->list.elements[i];
        }
    }
    return args->list.elements[args->list.count - 1];
}

f_object _call_reference(void *UNUSED(self), f_object args) {
    _check_length(args, 1);
    return reference(args->list.elements[0]);
}

f_object _call_not(void *UNUSED(self), f_object args) {
    _check_length(args, 1);
    return truthy(args->list.elements[0]) ? false_object : true_object;
}

f_object _call_foreach(void *UNUSED(self), f_object args) {
    if (args->list.count < 2) {
        errorf("Not enough arguments for foreach");
    }
    f_object code_block = args->list.elements[0];
    _check_type(code_block, CALLABLE);
    size_t list_count = args->list.count - 1;
    f_object main_list = args->list.elements[1];
    for (size_t i = 1; i < list_count; i++) {
        _check_type(args->list.elements[i], LIST);
        if (args->list.elements[i]->list.count != main_list->list.count) {
            errorf("List of uneven length in foreach");
        }
    }
    f_object inner_args = list(list_count);
    for (size_t i = 0; i < main_list->list.count; i++) {
        for (size_t j = 0; j < list_count; j++) {
            inner_args->list.elements[j] = args->list.elements[1 + j]->list.elements[i];
        }
        call(code_block, inner_args);
    }
    return none_object;
}

f_object _call_while(void *UNUSED(self), f_object args) {
    _check_length(args, 2);
    f_object condition = args->list.elements[0];
    f_object body = args->list.elements[1];
    while (truthy(call(condition, list(0)))) {
        call(body, list(0));
    }
    return none_object;
}

f_object _call_withOpenFile(void *UNUSED(self), f_object args) {
    _check_length(args, 3);

    f_object code_block = args->list.elements[0];
    _check_type(code_block, CALLABLE);

    f_object file_name = args->list.elements[1];
    _check_type(file_name, STRING);

    f_object file_mode = args->list.elements[2];
    _check_type(file_mode, STRING);

    f_object file = create(FILE_OBJECT);
    file->file.file_ptr = fopen(file_name->string, file_mode->string);
    if (file->file.file_ptr == NULL) {
        errorf("Can't open file '%s' with mode '%s'. errno: %i\n", file_name->string, file_mode->string, errno);
    }
    file->file.name = file_name->string;
    f_object out = call(code_block, list_v(1, file));
    if (fclose(file->file.file_ptr) == EOF) {
        errorf("Can't close file '%s' with mode '%s'. errno: %i\n", file_name->string, file_mode->string, errno);
    }
    return out;
}

f_object _call_writeLine(void *UNUSED(self), f_object args) {
    _check_length(args, 2);

    f_object file = args->list.elements[0];
    _check_type(file, FILE_OBJECT);

    f_object line = args->list.elements[1];
    _check_type(line, STRING);

    if (fprintf(file->file.file_ptr, "%s\n", line->string) < 0) {
        errorf("Couldn't write to file '%s'", file->file.name);
    }
    return none_object;
}

struct {
    f_object print;
    f_object either;
    f_object do_;
    f_object any;
    f_object and;
    f_object all;
    f_object or;
    f_object reference;
    f_object _dot_dot_dot;
    f_object false_;
    f_object true_;
    f_object not;
    f_object foreach;
    f_object while_;
    f_object withOpenFile;
    f_object writeLine;
} builtins;

//endregion

void setup_operators() {
    operators.semicolon = create_from((struct object) {.type=CALLABLE, .callable.func=_call_semicolon});

    operators.add = create_from((struct object) {.type=CALLABLE, .callable.func=_call_add});
    operators.sub = create_from((struct object) {.type=CALLABLE, .callable.func=_call_sub});
    operators.mul = create_from((struct object) {.type=CALLABLE, .callable.func=_call_mul});
    operators.div = create_from((struct object) {.type=CALLABLE, .callable.func=_call_div});
    operators.pow = create_from((struct object) {.type=CALLABLE, .callable.func=_call_pow});

    operators.eq = create_from((struct object) {.type=CALLABLE, .callable.func=_call_eq});
    operators.ne = create_from((struct object) {.type=CALLABLE, .callable.func=_call_ne});
    operators.gt = create_from((struct object) {.type=CALLABLE, .callable.func=_call_gt});
    operators.ge = create_from((struct object) {.type=CALLABLE, .callable.func=_call_ge});
    operators.lt = create_from((struct object) {.type=CALLABLE, .callable.func=_call_lt});
    operators.le = create_from((struct object) {.type=CALLABLE, .callable.func=_call_le});

    operators.store = create_from((struct object) {.type=CALLABLE, .callable.func=_call_store});
    operators.load = create_from((struct object) {.type=CALLABLE, .callable.func=_call_load});
}

void setup_builtins() {
    builtins.print = callable(NULL, _call_print);
    builtins.either = callable(NULL, _call_either);
    builtins.do_ = callable(NULL, _call_do);
    builtins.any = callable(NULL, _call_any);
    builtins.or = callable(NULL, _call_any);
    builtins.all = callable(NULL, _call_all);
    builtins.and = callable(NULL, _call_all);
    builtins.reference = callable(NULL, _call_reference);
    builtins.false_ = false_object;
    builtins.true_ = true_object;
    builtins.not = callable(NULL, _call_not);
    builtins.foreach = callable(NULL, _call_foreach);
    builtins.while_ = callable(NULL, _call_while);
    builtins.withOpenFile = callable(NULL, _call_withOpenFile);
    builtins.writeLine = callable(NULL, _call_writeLine);
}

void setup(int argc, char **argv) {
    none_object = create_from((struct object) {.type=NONE});
    false_object = create_from((struct object) {.type=NUMBER, .number=0});
    true_object = create_from((struct object) {.type=NUMBER, .number=1});

    setup_builtins();
    setup_operators();

    builtins._dot_dot_dot = list((size_t) (argc - 1));
    for (size_t i = 1; i < argc; i++) {
        builtins._dot_dot_dot->list.elements[i - 1] = create_from((struct object) {.type=STRING, .string=argv[i]});
    }
}