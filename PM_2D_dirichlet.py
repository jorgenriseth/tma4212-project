import numpy as np
import matplotlib.pyplot as plt
import scipy.sparse as spsp
import scipy.sparse.linalg as spla

import diffusions as func
from schemes import *
from PIL import Image

# Load image from file to numpy array
def load_image( infilename , size = None) :
    img = Image.open( infilename )
    img.load()
    if size:
        img = img.resize(size)
    data = np.asarray( img, dtype="float32" )
    return data
    
    
    
# Display image given vector representation, and dimensions
def array_to_image(V, m, n):
    if len(V.shape) == 2:
        image = V.reshape((m, n, 3))
        return Image.fromarray(image.astype("uint8"), "RGB")

    else:
        image = V.reshape((m, n))
        return Image.fromarray(image.astype("uint8"), "L")
        
        
        
# Generate image of 4 scaled squares
def generate_squares2D(N, M):
    I = np.zeros((N+2, M+2))
    I[:N//2+1, :M//2+1] = 80
    I[:N//2+1, -(M//2+1):] = 190
    I[-(N//2+1):, :M//2+1] = 140
    I[-(N//2+1):, -(M//2+1):] = 230
    return I



# Add noise to all interior points of an image
def add_noise2D(I, scale = 10):
    if len(I.shape) == 3:
        M, N = I[:, :, 0].shape
    else:
        M, N = I.shape

    M -= 2
    N -= 2

    if len(I.shape) == 3:
        I[1:-1, 1:-1] += np.random.randint(-scale, scale, size = (M, N, 3))
    else:
        I[1:-1, 1:-1] += np.random.randint(-scale, scale, size = (M,N))
    #return np.minimum(np.maximum(0, I), 255)
    return I
    
    
    
    
# Generate square image, with noise
def generate_random2D(M, N, scale = 10):
    I = generate_squares2D(N, M)
    add_noise2D(I)
    return I



# Plot progression of image in 6 pictures.
def before_after_2D(U, N, M, savename = None, display = True):
    skip = U.shape[0]//5
    plt.figure()
    if (len(U.shape) == 3):
        plt.subplot(2, 3, 1)
        im = array_to_image(U[0], N+2, M+2)
        plt.imshow(im)
        for i in range(2, 6):            
            plt.subplot(2, 3, i)
            im = array_to_image(U[(i-1)*skip], N+2, M+2)
            plt.imshow(im)
        plt.subplot(236)
        im = array_to_image(U[-1], N+2, M+2)
        plt.imshow(im)

    else:
        plt.subplot(2, 3, 1)
        im = array_to_image(U[0], N+2, M+2)
        plt.imshow(im, cmap = "gray")
        for i in range(2, 6):            
            plt.subplot(2, 3, i)
            im = array_to_image(U[(i-1)*skip], N+2, M+2)
            plt.imshow(im, cmap = "gray")
        plt.subplot(2, 3, 6)
        im = array_to_image(U[-1], N+2, M+2)
        plt.imshow(im, cmap = "gray")

    if savename:
        plt.savefig(savename)

    if display:
        plt.show()
        

# Print current picture while iterating
def iteration_echo(M, N, G, u):
    K = (M+2)*(N+2)

    plt.figure(figsize=(12, 8))
    plt.subplot(121)
    plt.imshow(u.reshape(N+2, M+2), cmap = "gray", vmin = 0, vmax = 255)
    
    plt.subplot(122)
    plt.imshow(G.reshape(N+2, M+2), cmap = "gray")

    plt.show()



# Explicit solver for difference scheme
def solve_FE(u0, g, M, N, T, dt, echo = False):
    dx = 1/(M+1)
    dy = 1/(N+1)
    K = (M+2)*(N+2)
    
    U = np.zeros((T, K))
    U[0] = u0   
    
    Dx = diffX(M, N)
    Dy = diffY(M, N)
    
    Ξx, Ωx, Γx = support_matrices_X(M, N)
    Ξy, Ωy, Γy = support_matrices_Y(M, N)
    
    for it in range(T-1):
        A = assemble_A(U[it], M, N, g, Dx, Dy, Ξx, Ωx, Γx, Ξy, Ωy, Γy)
        U[it+1] = U[it] + dt * A.dot(U[it])
        
        if echo:
            if it % (T//10) == 0:
                G = g(Dx.dot(U[it])**2 + Dy.dot(U[it])**2)
                iteration_echo(M, N, G, U[it])            
    return U


# Semi-implicit(Backward Euler), solver for difference scheme
def solve_BE(u0, g, M, N, T, dt, echo = False):
    dx = 1/(M+1)
    dy = 1/(N+1)
    K = (M+2)*(N+2)

    U = np.zeros((T, K))
    U[0] = u0   
    
    Dx = diffX(M, N)
    Dy = diffY(M, N)
    
    Ξx, Ωx, Γx = support_matrices_X(M, N)
    Ξy, Ωy, Γy = support_matrices_Y(M, N)

    for it in range(T-1):
        A = assemble_A(U[it], M, N, g, Dx, Dy, Ξx, Ωx, Γx, Ξy, Ωy, Γy)
        U[it+1] = spla.spsolve(spsp.identity((M+2)*(N+2)) - dt * A, U[it])
        
        if echo:
            if it % (T//10) == 0:
                G = g(Dx.dot(U[it])**2 + Dy.dot(U[it])**2)
                iteration_echo(M, N, G, U[it])
    return U


# Semi-implicit(Crank-Nicholson) solver for difference scheme
def solve_CN(u0, g, M, N, T, dt, echo = False):
    dx = 1/(M+1)
    dy = 1/(N+1)
    K = (M+2)*(N+2)

    U = np.zeros((T, K))
    U[0] = u0   
    
    Dx = diffX(M, N)
    Dy = diffY(M, N)
    
    Ξx, Ωx, Γx = support_matrices_X(M, N)
    Ξy, Ωy, Γy = support_matrices_Y(M, N)

    for it in range(T-1):
        A = assemble_A(U[it], M, N, g, Dx, Dy, Ξx, Ωx, Γx, Ξy, Ωy, Γy)
        U[it+1] = spla.spsolve(spsp.identity((M+2)*(N+2)) - dt/2 * A, (spsp.identity((M+2)*(N+2)) + dt/2 *A).dot(U[it]))
        
        if echo:
            if it % (T/10) == 0:
                G = g(Dx.dot(U[it])**2 + Dy.dot(U[it])**2)
                iteration_echo(M, N, G, U[it])

    return U

def solve_RGB_BE(u0, g, M, N, T, dt, echo = False):
    dx = 1/(M+1)
    dy = 1/(N+1)
    K = (M+2)*(N+2)
    

    U = np.zeros((T, K, 3))
    U[0] = u0
    
    Dx = diffX(M, N)
    Dy = diffY(M, N)
    
    Ξx, Ωx, Γx = support_matrices_X(M, N)
    Ξy, Ωy, Γy = support_matrices_Y(M, N)

    for it in range(T-1):
        Ar = assemble_A(U[it,:, 0], M, N, g, Dx, Dy, Ξx, Ωx, Γx, Ξy, Ωy, Γy)
        Ag = assemble_A(U[it,:, 1], M, N, g, Dx, Dy, Ξx, Ωx, Γx, Ξy, Ωy, Γy)
        Ab = assemble_A(U[it,:, 2], M, N, g, Dx, Dy, Ξx, Ωx, Γx, Ξy, Ωy, Γy)
        
        U[it+1,:, 0] = spla.spsolve(spsp.identity((M+2)*(N+2)) - dt * Ar, U[it, :, 0])
        U[it+1,:, 1] = spla.spsolve(spsp.identity((M+2)*(N+2)) - dt * Ag, U[it, :, 1])
        U[it+1,:, 2] = spla.spsolve(spsp.identity((M+2)*(N+2)) - dt * Ab, U[it, :, 2])

        if echo:
            if it % (T//10) == 0:
                im = array_to_image(U[it], N+2, M+2)
                plt.imshow(im)
                plt.show()
    return U

def F(x, y, alpha):
    smooth = np.tanh(alpha*x) + np.tanh(alpha*y)
    noiseX = 0.1*np.sin(5*x)**2 * np.sin(50*x)
    noiseU = 0.1*np.sin(5*y)**2 * np.sin(50*y)
    return smooth + noiseX + noiseY

def savename(image_name, M, N, T, dt, funcname):
    name = "./figures/"
    name += str(M) + "x" + str(N) + "_"
    name += str(T) + "_" + str(dt) + "_"
    name += str(funcname) + "-"
    return name + image_name 


if __name__== "__main__":
    M, N = 128, 128
    K = (M+2) * (N+2)

    T = 200
    dt = 1

    c = 1
    diffusion = 0
    g = func.choose_function(diffusion, c)


    imname = "pgv1a.jpg"
    I = load_image("./images/"+imname, (M+2, N+2))
    I = add_noise2D(I, scale = 35)
    U = solve_RGB_BE(I.reshape(K, 3), g, M, N, T, dt, echo = False)
    before_after_2D(U, N, M, savename = savename(imname, M+2, N+2, T, dt, diffusion))

    imname = "lena-128x128.jpg"
    I = load_image("./images/"+imname, (M+2, N+2))
    I = add_noise2D(I, scale = 40)
    U = solve_BE(I.reshape(K), g, M, N, T, dt)
    before_after_2D(U, N, M, savename = savename(imname, M+2, N+2, T, dt))

    imname = "dali.jpg"
    I = load_image("./images/"+imname, (M+2, N+2))
    I = add_noise2D(I, scale = 35)
    U = solve_RGB_BE(I.reshape(K, 3), g, M, N, T, dt)
    before_after_2D(U, N, M, savename = savename(imname, M+2, N+2, T, dt))
