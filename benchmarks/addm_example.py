import numpy as np
from scipy.optimize import minimize

# Define the objective function
def objective_function(x):
    return x[0]**2 + x[1]**2

# Define the equality constraint function
def equality_constraint(x):
    return x[0] + x[1] - 1

# Define the augmented Lagrangian function
def augmented_lagrangian(x, rho, lambd):
    return objective_function(x) + rho/2 * equality_constraint(x)**2 + np.dot(lambd, equality_constraint(x))

# # Define the gradient of the augmented Lagrangian function
# def augmented_lagrangian_gradient(x, rho, lambd):
#     grad_obj = np.array([2*x[0], 2*x[1]])
#     grad_eq_const = np.array([1, 1])
#     return grad_obj + rho * equality_constraint(x) * grad_eq_const + lambd * grad_eq_const
# Define the augmented Lagrangian function
def augmented_lagrangian(x, rho, lambd):
    obj_value = objective_function(x)
    equality_const = equality_constraint(x)
    return obj_value + rho/2 * equality_const**2 + np.dot(lambd, equality_const)


# Define the ADMM algorithm
def admm(initial_guess, rho, alpha, max_iter):
    x = initial_guess
    lambd = np.zeros_like(initial_guess)
    
    for _ in range(max_iter):
        x = minimize(lambda x: augmented_lagrangian(x, rho, lambd), x, method='BFGS', jac=lambda x: augmented_lagrangian_gradient(x, rho, lambd)).x
        lambd = lambd + alpha * equality_constraint(x)
    
    return x

# Set initial guess, penalty parameter, step size, and maximum iterations
initial_guess = np.array([0.5, 0.5])
rho = 1.0
alpha = 0.1
max_iter = 100

# Run the ADMM algorithm
result = admm(initial_guess, rho, alpha, max_iter)

print("Optimal solution:", result)
print("Objective value:", objective_function(result))
