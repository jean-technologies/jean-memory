"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/contexts/AuthContext";
import { useProfile } from "@/hooks/useProfile";
import { LogOut, Settings, Code, Star, MessageSquare, Book, ShieldCheck } from "lucide-react";
import { RiApps2AddFill } from "react-icons/ri";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Icons } from "./icons";

export function UserNav() {
  const { user, signOut } = useAuth();
  const { profile, getDisplayName } = useProfile();
  const router = useRouter();

  if (!user) {
    return null;
  }

  const displayName = getDisplayName() || user.user_metadata.full_name || user.email?.split('@')[0] || 'User';

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-8 w-8 rounded-full">
          <Avatar className="h-8 w-8">
            <AvatarImage src={user.user_metadata.avatar_url} alt={user.user_metadata.full_name ?? "User"} />
            <AvatarFallback>{user.email?.[0].toUpperCase()}</AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{displayName}</p>
            <p className="text-xs leading-none text-muted-foreground">
              {user.email}
            </p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <Link href="/settings">
            <DropdownMenuItem>
              <Settings className="mr-2 h-4 w-4" />
              <span>Settings</span>
            </DropdownMenuItem>
          </Link>
          <Link href="/privacy">
            <DropdownMenuItem>
              <ShieldCheck className="mr-2 h-4 w-4" />
              <span>Privacy</span>
            </DropdownMenuItem>
          </Link>
          <Link href="/api-docs">
            <DropdownMenuItem>
              <Book className="mr-2 h-4 w-4" />
              <span>API Docs</span>
            </DropdownMenuItem>
          </Link>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <a href="https://github.com/jonathan-politzki/your-memory" target="_blank" rel="noopener noreferrer">
          <DropdownMenuItem>
            <Icons.github className="mr-2 h-4 w-4" />
            <span>GitHub</span>
          </DropdownMenuItem>
        </a>
        <a href="https://discord.gg/2Qn4xgU9tn" target="_blank" rel="noopener noreferrer">
          <DropdownMenuItem>
            <MessageSquare className="mr-2 h-4 w-4" />
            <span>Discord</span>
          </DropdownMenuItem>
        </a>
        <a href="https://buy.stripe.com/8x214n2K0cmVadx3pIabK01" target="_blank" rel="noopener noreferrer">
          <DropdownMenuItem>
            <Star className="mr-2 h-4 w-4" />
            <span>Pro</span>
          </DropdownMenuItem>
        </a>
        <Link href="/apps">
          <DropdownMenuItem>
            <RiApps2AddFill className="mr-2 h-4 w-4" />
            <span>Apps</span>
          </DropdownMenuItem>
        </Link>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={async () => {
          await signOut();
          router.push('/auth');
        }}>
          <LogOut className="mr-2 h-4 w-4" />
          <span>Log out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
} 