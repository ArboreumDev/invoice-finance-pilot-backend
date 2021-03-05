import {
  Flex,
  Box,
  Heading,
  FormControl,
  FormLabel,
  Input,
  Button,
} from "@chakra-ui/react";
import Router from "next/dist/next-server/lib/router/router";
import React, { useState } from "react";
import { useRouter } from "next/router";
import {fetcher, axiosInstance} from "../components/Main"

export default function Login() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const handleSubmit = async (event) => {
    event.preventDefault();
    // const { data: profits, error: profitError } = useSWR('/profit', fetcher, { refreshInterval: 1000 })
    var bodyFormData = new FormData();
    bodyFormData.append('username', email);
    bodyFormData.append('password', password);
    try {
      const res = await axiosInstance.post("/token", bodyFormData)
      console.log('loginres', res)
      if (res.status === 200) {
        window.localStorage.setItem("arboreum:info", JSON.stringify({
          token: res.data.access_token,
          role: res.data.role,
          email: email
        }))
        console.log('login success')
        router.push("/");
      } else {
        console.log("some error!", res.data)
      }
    } catch {
      alert("wrong pw")
    }
  };
  return (
    <Flex width="full" align="center" justifyContent="center">
      <Box p={2}>
        <Box textAlign="center">
          <Heading>Login</Heading>
        </Box>
        <Box
          p={8}
          maxWidth="500px"
          borderWidth={1}
          borderRadius={8}
          boxShadow="lg"
        >
          <form onSubmit={handleSubmit}>
            <FormControl>
              <FormLabel>Email</FormLabel>
              <Input
                type="username"
                // type="email"
                placeholder="test@test.com"
                size="lg"
                onChange={(event) => setEmail(event.currentTarget.value)}
              />
            </FormControl>
            <FormControl mt={6}>
              <FormLabel>Password</FormLabel>
              <Input
                type="password"
                placeholder="*******"
                onChange={(event) => setPassword(event.currentTarget.value)}
              />
            </FormControl>
            {/* <Button width="full" mt={4} type="submit"> */}
            <Button
              type="submit"
              variantColor="teal"
              variant="outline"
              width="full"
              mt={4}
            >
              Sign In
            </Button>
          </form>
        </Box>
      </Box>
    </Flex>
  );
}
